import { Router, type IRouter } from "express";
import {
  and,
  asc,
  desc,
  eq,
  or,
  sql,
} from "drizzle-orm";
import {
  db,
  pool,
  categoriesTable,
  productsTable,
  inventoryItemsTable,
  stockMovementsTable,
  customersTable,
  ordersTable,
  orderItemsTable,
  usersTable,
} from "@workspace/db";
import {
  createToken,
  hashPassword,
  requireAdmin,
  requireUser,
  verifyPassword,
} from "../lib/auth";

const router: IRouter = Router();
const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const categoryJson = (row: typeof categoriesTable.$inferSelect) => ({
  id: row.id,
  name: row.name,
  slug: row.slug,
  description: row.description,
  is_active: row.isActive,
});

const productJson = (row: typeof productsTable.$inferSelect) => ({
  id: row.id,
  category_id: row.categoryId,
  name: row.name,
  slug: row.slug,
  sku: row.sku,
  description: row.description,
  price: row.price,
  is_active: row.isActive,
});

router.get("/v1/catalog/categories", async (_req, res): Promise<void> => {
  const rows = await db
    .select()
    .from(categoriesTable)
    .where(eq(categoriesTable.isActive, true))
    .orderBy(asc(categoriesTable.name));
  res.json(rows.map(categoryJson));
});

router.post(
  "/v1/catalog/categories",
  requireAdmin,
  async (req, res): Promise<void> => {
    const name = String(req.body?.name ?? "").trim();
    const slug = String(req.body?.slug ?? "").trim();
    if (!name || name.length > 120 || !slugPattern.test(slug)) {
      res.status(422).json({ error: "Invalid category" });
      return;
    }
    try {
      const [row] = await db
        .insert(categoriesTable)
        .values({ name, slug, description: req.body?.description || null })
        .returning();
      res.status(201).json(categoryJson(row));
    } catch {
      res.status(409).json({ error: "Category already exists" });
    }
  },
);

router.get("/v1/catalog/products", async (req, res): Promise<void> => {
  const categoryId =
    typeof req.query.category_id === "string" ? req.query.category_id : null;
  const where = categoryId
    ? and(
        eq(productsTable.isActive, true),
        eq(productsTable.categoryId, categoryId),
      )
    : eq(productsTable.isActive, true);
  const rows = await db
    .select()
    .from(productsTable)
    .where(where)
    .orderBy(asc(productsTable.name));
  res.json(rows.map(productJson));
});

router.get(
  "/v1/catalog/products/manage",
  requireAdmin,
  async (_req, res): Promise<void> => {
    const rows = await db
      .select()
      .from(productsTable)
      .orderBy(asc(productsTable.name));
    res.json(rows.map(productJson));
  },
);

router.get("/v1/catalog/products/:id", async (req, res): Promise<void> => {
  const [row] = await db
    .select()
    .from(productsTable)
    .where(
      and(
        eq(productsTable.id, String(req.params.id)),
        eq(productsTable.isActive, true),
      ),
    );
  if (!row) {
    res.status(404).json({ error: "Product not found" });
    return;
  }
  res.json(productJson(row));
});

router.post(
  "/v1/catalog/products",
  requireAdmin,
  async (req, res): Promise<void> => {
    const input = req.body ?? {};
    const name = String(input.name ?? "").trim();
    const slug = String(input.slug ?? "").trim();
    const sku = String(input.sku ?? "").trim();
    const price = Number(input.price);
    if (
      !name ||
      !slugPattern.test(slug) ||
      !sku ||
      !input.category_id ||
      !Number.isFinite(price) ||
      price < 0
    ) {
      res.status(422).json({ error: "Invalid product" });
      return;
    }
    const [category] = await db
      .select()
      .from(categoriesTable)
      .where(eq(categoriesTable.id, input.category_id));
    if (!category) {
      res.status(400).json({ error: "Category not found" });
      return;
    }
    try {
      const [row] = await db
        .insert(productsTable)
        .values({
          categoryId: input.category_id,
          name,
          slug,
          sku,
          description: input.description || null,
          price: price.toFixed(2),
        })
        .returning();
      await db
        .insert(inventoryItemsTable)
        .values({ productId: row.id })
        .onConflictDoNothing();
      res.status(201).json(productJson(row));
    } catch {
      res.status(409).json({ error: "Product slug or SKU already exists" });
    }
  },
);

router.patch(
  "/v1/catalog/products/:id",
  requireAdmin,
  async (req, res): Promise<void> => {
    const values: Partial<typeof productsTable.$inferInsert> = {};
    if (typeof req.body?.is_active === "boolean")
      values.isActive = req.body.is_active;
    if (typeof req.body?.name === "string") values.name = req.body.name.trim();
    if (typeof req.body?.description === "string")
      values.description = req.body.description;
    const [row] = await db
      .update(productsTable)
      .set(values)
      .where(eq(productsTable.id, String(req.params.id)))
      .returning();
    if (!row) {
      res.status(404).json({ error: "Product not found" });
      return;
    }
    res.json(productJson(row));
  },
);

router.post("/v1/customers", async (req, res): Promise<void> => {
  const fullName = String(req.body?.full_name ?? "").trim();
  const email = String(req.body?.email ?? "").trim().toLowerCase() || null;
  const phone = String(req.body?.phone ?? "").trim() || null;
  if (!fullName || (!email && !phone)) {
    res.status(422).json({ error: "Name and email or phone are required" });
    return;
  }
  const conditions = [
    email ? eq(customersTable.email, email) : undefined,
    phone ? eq(customersTable.phone, phone) : undefined,
  ].filter(Boolean) as ReturnType<typeof eq>[];
  const [existing] = await db
    .select()
    .from(customersTable)
    .where(or(...conditions));
  if (existing) {
    res.status(409).json({ error: "Customer already exists" });
    return;
  }
  try {
    const [row] = await db
      .insert(customersTable)
      .values({ fullName, email, phone })
      .returning();
    res.status(201).json({
      id: row.id,
      full_name: row.fullName,
      email: row.email,
      phone: row.phone,
    });
  } catch {
    res.status(409).json({ error: "Customer already exists" });
  }
});

router.get(
  "/v1/customers/lookup",
  requireAdmin,
  async (req, res): Promise<void> => {
  const phone =
    typeof req.query.phone === "string" ? req.query.phone.trim() : "";
  const email =
    typeof req.query.email === "string"
      ? req.query.email.trim().toLowerCase()
      : "";
  if (!phone && !email) {
    res.status(422).json({ error: "Email or phone is required" });
    return;
  }
  const where = and(
    phone ? eq(customersTable.phone, phone) : undefined,
    email ? eq(customersTable.email, email) : undefined,
  );
  const rows = await db.select().from(customersTable).where(where).limit(20);
  res.json(
    rows.map((row) => ({
      id: row.id,
    })),
  );
  },
);

router.get("/v1/inventory", requireAdmin, async (_req, res): Promise<void> => {
  const rows = await db
    .select({
      productId: inventoryItemsTable.productId,
      quantity: inventoryItemsTable.quantity,
      reorderLevel: inventoryItemsTable.reorderLevel,
    })
    .from(inventoryItemsTable)
    .innerJoin(
      productsTable,
      and(
        eq(productsTable.id, inventoryItemsTable.productId),
        eq(productsTable.isActive, true),
      ),
    )
    .orderBy(desc(inventoryItemsTable.updatedAt));
  res.json(
    rows.map((row) => ({
      product_id: row.productId,
      quantity: row.quantity,
      reorder_level: row.reorderLevel,
      low_stock: row.quantity <= row.reorderLevel,
    })),
  );
});

router.post(
  "/v1/inventory/:productId/adjust",
  requireAdmin,
  async (req, res): Promise<void> => {
    const productId = String(req.params.productId);
    const delta = Number(req.body?.delta);
    const reason = String(req.body?.reason ?? "").trim();
    if (!Number.isInteger(delta) || !reason) {
      res.status(422).json({ error: "Invalid adjustment" });
      return;
    }
    const client = await pool.connect();
    try {
      await client.query("BEGIN");
      const product = await client.query(
        "SELECT id FROM products WHERE id = $1 AND is_active = true",
        [productId],
      );
      if (!product.rowCount) {
        await client.query("ROLLBACK");
        res.status(404).json({ error: "Product not found" });
        return;
      }
      await client.query(
        "INSERT INTO inventory_items (id, product_id, quantity, reorder_level) VALUES (gen_random_uuid(), $1, 0, 5) ON CONFLICT (product_id) DO NOTHING",
        [productId],
      );
      const current = await client.query(
        "SELECT id, quantity, reorder_level FROM inventory_items WHERE product_id = $1 FOR UPDATE",
        [productId],
      );
      const next = Number(current.rows[0].quantity) + delta;
      if (next < 0) {
        await client.query("ROLLBACK");
        res.status(409).json({ error: "Inventory cannot be negative" });
        return;
      }
      await client.query(
        "UPDATE inventory_items SET quantity = $1, updated_at = NOW() WHERE id = $2",
        [next, current.rows[0].id],
      );
      await client.query(
        "INSERT INTO stock_movements (id, inventory_id, delta, reason) VALUES (gen_random_uuid(), $1, $2, $3)",
        [current.rows[0].id, delta, reason],
      );
      await client.query("COMMIT");
      res.json({
        product_id: productId,
        quantity: next,
        reorder_level: current.rows[0].reorder_level,
        low_stock: next <= Number(current.rows[0].reorder_level),
      });
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  },
);

router.post("/v1/orders", async (req, res): Promise<void> => {
  const { customer_id, customer_name, customer_phone, items } = req.body ?? {};
  if (
    !String(customer_name ?? "").trim() ||
    String(customer_phone ?? "").trim().length < 5 ||
    !Array.isArray(items) ||
    items.length < 1
  ) {
    res.status(422).json({ error: "Invalid order" });
    return;
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    if (customer_id) {
      const customer = await client.query(
        "SELECT id FROM customers WHERE id = $1",
        [customer_id],
      );
      if (!customer.rowCount) {
        await client.query("ROLLBACK");
        res.status(400).json({ error: "Customer not found" });
        return;
      }
    }
    let total = 0;
    const lines: Array<{
      productId: string;
      quantity: number;
      unitPrice: string;
    }> = [];
    for (const raw of items) {
      const quantity = Number(raw.quantity);
      if (!raw.product_id || !Number.isInteger(quantity) || quantity < 1 || quantity > 999) {
        await client.query("ROLLBACK");
        res.status(422).json({ error: "Invalid order item" });
        return;
      }
      const product = await client.query(
        `SELECT p.id, p.price, i.id AS inventory_id, i.quantity AS stock
         FROM products p JOIN inventory_items i ON i.product_id = p.id
         WHERE p.id = $1 AND p.is_active = true FOR UPDATE OF i`,
        [raw.product_id],
      );
      if (!product.rowCount) {
        await client.query("ROLLBACK");
        res.status(400).json({ error: "Product not found" });
        return;
      }
      if (Number(product.rows[0].stock ?? 0) < quantity) {
        await client.query("ROLLBACK");
        res.status(409).json({ error: "Insufficient stock" });
        return;
      }
      await client.query(
        "UPDATE inventory_items SET quantity = quantity - $1, updated_at = NOW() WHERE id = $2",
        [quantity, product.rows[0].inventory_id],
      );
      const unitPrice = String(product.rows[0].price);
      total += Number(unitPrice) * quantity;
      lines.push({ productId: raw.product_id, quantity, unitPrice });
    }
    const order = await client.query(
      `INSERT INTO orders (id, customer_id, customer_name, customer_phone, status, total)
       VALUES (gen_random_uuid(), $1, $2, $3, 'pending', $4) RETURNING id, customer_id, status, total, customer_name, customer_phone, created_at`,
      [customer_id || null, customer_name.trim(), customer_phone.trim(), total.toFixed(2)],
    );
    for (const line of lines) {
      await client.query(
        `INSERT INTO order_items (id, order_id, product_id, quantity, unit_price)
         VALUES (gen_random_uuid(), $1, $2, $3, $4)`,
        [order.rows[0].id, line.productId, line.quantity, line.unitPrice],
      );
    }
    await client.query("COMMIT");
    res.status(201).json(order.rows[0]);
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
});

router.get("/v1/orders", requireAdmin, async (_req, res): Promise<void> => {
  const rows = await db
    .select()
    .from(ordersTable)
    .orderBy(desc(ordersTable.createdAt))
    .limit(100);
  res.json(
    rows.map((row) => ({
      id: row.id,
      customer_id: row.customerId,
      customer_name: row.customerName,
      customer_phone: row.customerPhone,
      status: row.status,
      total: row.total,
      created_at: row.createdAt,
    })),
  );
});

router.post("/v1/auth/register", async (req, res): Promise<void> => {
  const email = String(req.body?.email ?? "").trim().toLowerCase();
  const password = String(req.body?.password ?? "");
  if (!email || password.length < 8 || password.length > 128) {
    res.status(422).json({ error: "Invalid email or password" });
    return;
  }
  try {
    const [user] = await db
      .insert(usersTable)
      .values({
        email,
        passwordHash: hashPassword(password),
        role: "customer",
      })
      .returning();
    res.status(201).json({ id: user.id, email: user.email, role: user.role });
  } catch {
    res.status(409).json({ error: "Account already exists" });
  }
});

router.post("/v1/auth/bootstrap-admin", async (req, res): Promise<void> => {
  const configured = process.env.SESSION_SECRET ?? "";
  const supplied = req.header("x-admin-setup-secret") ?? "";
  if (!configured || supplied.length !== configured.length) {
    res.status(403).json({ error: "Invalid setup secret" });
    return;
  }
  const { timingSafeEqual } = await import("node:crypto");
  if (!timingSafeEqual(Buffer.from(supplied), Buffer.from(configured))) {
    res.status(403).json({ error: "Invalid setup secret" });
    return;
  }
  const email = String(req.body?.email ?? "").trim().toLowerCase();
  const password = String(req.body?.password ?? "");
  if (!email || password.length < 8 || password.length > 128) {
    res.status(422).json({ error: "Invalid email or password" });
    return;
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("LOCK TABLE users IN EXCLUSIVE MODE");
    const existingAdmin = await client.query(
      "SELECT id FROM users WHERE role = 'admin' LIMIT 1",
    );
    if (existingAdmin.rowCount) {
      await client.query("ROLLBACK");
      res.status(409).json({ error: "An admin account is already provisioned" });
      return;
    }
    const result = await client.query(
      `INSERT INTO users (id, email, password_hash, role, is_active)
       VALUES (gen_random_uuid(), $1, $2, 'admin', true)
       ON CONFLICT (email) DO UPDATE
       SET password_hash = EXCLUDED.password_hash, role = 'admin', is_active = true
       RETURNING id, email, role`,
      [email, hashPassword(password)],
    );
    await client.query("COMMIT");
    res.status(201).json(result.rows[0]);
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
});

router.post("/v1/auth/login", async (req, res): Promise<void> => {
  const email = String(req.body?.email ?? "").trim().toLowerCase();
  const password = String(req.body?.password ?? "");
  const [user] = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.email, email));
  if (!user?.isActive || !verifyPassword(password, user.passwordHash)) {
    res.status(401).json({ error: "Invalid email or password" });
    return;
  }
  res.json({
    access_token: createToken(user),
    token_type: "bearer",
    user: { id: user.id, email: user.email, role: user.role },
  });
});

router.get("/v1/auth/me", requireUser, async (req, res): Promise<void> => {
  const user = req.currentUser!;
  res.json({ id: user.id, email: user.email, role: user.role });
});

router.get("/v1/foundation", (_req, res) => {
  res.json({ status: "ok", message: "My Case v1 API foundation" });
});

export default router;