import { createHmac, timingSafeEqual } from "node:crypto";
import { Router, type IRouter, type Request, type Response } from "express";
import { pool } from "@workspace/db";

const router: IRouter = Router();

type TelegramUser = { id: string; username: string | null };

function secureEqual(left: string, right: string): boolean {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

function validateInitData(initData: string, botToken: string): TelegramUser {
  const params = new URLSearchParams(initData);
  const receivedHash = params.get("hash") ?? "";
  params.delete("hash");
  if (!receivedHash || params.size === 0) throw new Error("incomplete");
  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");
  const secretKey = createHmac("sha256", "WebAppData")
    .update(botToken)
    .digest();
  const expected = createHmac("sha256", secretKey)
    .update(dataCheckString)
    .digest("hex");
  if (!secureEqual(receivedHash, expected)) throw new Error("signature");
  const authDate = Number(params.get("auth_date"));
  if (
    !Number.isFinite(authDate) ||
    authDate <= 0 ||
    Date.now() / 1000 - authDate > 86_400
  )
    throw new Error("expired");
  const user = JSON.parse(params.get("user") ?? "{}");
  if (!user.id) throw new Error("user");
  return { id: String(user.id), username: user.username ?? null };
}

function telegramUser(req: Request, res: Response): TelegramUser | null {
  const configured = (process.env.TELEGRAM_BOT_TOKEN ?? "").trim();
  const initData = req.header("x-telegram-init-data");
  if (initData) {
    if (!configured) {
      res.status(503).json({ error: "Telegram authentication is not configured" });
      return null;
    }
    try {
      return validateInitData(initData, configured);
    } catch {
      res.status(401).json({ error: "Invalid Telegram session" });
      return null;
    }
  }
  const token = req.header("x-telegram-bot-token") ?? "";
  const userId = req.header("x-telegram-user-id") ?? "";
  if (
    configured &&
    token &&
    /^\d+$/.test(userId) &&
    secureEqual(token, configured)
  )
    return { id: userId, username: null };
  res.status(401).json({ error: "Telegram authentication required" });
  return null;
}

async function linkedCustomer(
  req: Request,
  res: Response,
): Promise<{ id: string; fullName: string; phone: string } | null> {
  const user = telegramUser(req, res);
  if (!user) return null;
  const result = await pool.query(
    `SELECT c.id, c.full_name, c.phone
     FROM telegram_identities ti
     JOIN customers c ON c.id = ti.customer_id
     WHERE ti.provider = 'telegram' AND ti.provider_user_id = $1`,
    [user.id],
  );
  if (!result.rowCount) {
    res.status(409).json({ error: "Telegram account is not linked to a customer" });
    return null;
  }
  if (user.username) {
    await pool.query(
      `UPDATE telegram_identities
       SET username = $1, updated_at = NOW()
       WHERE provider = 'telegram' AND provider_user_id = $2`,
      [user.username, user.id],
    );
  }
  return {
    id: result.rows[0].id,
    fullName: result.rows[0].full_name,
    phone: result.rows[0].phone ?? "",
  };
}

async function ensureCart(customerId: string): Promise<string> {
  const result = await pool.query(
    `INSERT INTO carts (id, customer_id)
     VALUES (gen_random_uuid(), $1)
     ON CONFLICT (customer_id) DO UPDATE SET updated_at = NOW()
     RETURNING id`,
    [customerId],
  );
  return result.rows[0].id;
}

async function cartPayload(customerId: string) {
  const cartId = await ensureCart(customerId);
  const result = await pool.query(
    `SELECT p.id AS product_id, p.name AS product_name, p.sku,
            ci.quantity, p.price AS unit_price,
            (ci.quantity * p.price)::numeric(12,2) AS line_total
     FROM cart_items ci
     JOIN products p ON p.id = ci.product_id
     WHERE ci.cart_id = $1 AND p.is_active = true
     ORDER BY ci.created_at`,
    [cartId],
  );
  const total = result.rows
    .reduce((sum, row) => sum + Number(row.line_total), 0)
    .toFixed(2);
  return { customer_id: customerId, items: result.rows, total };
}

async function orderPayload(orderId: string, customerId: string) {
  const order = await pool.query(
    `SELECT id, status, total, created_at
     FROM orders WHERE id = $1 AND customer_id = $2`,
    [orderId, customerId],
  );
  if (!order.rowCount) return null;
  const items = await pool.query(
    `SELECT oi.product_id, p.name AS product_name, p.sku,
            oi.quantity, oi.unit_price
     FROM order_items oi JOIN products p ON p.id = oi.product_id
     WHERE oi.order_id = $1`,
    [orderId],
  );
  return { ...order.rows[0], items: items.rows };
}

router.post("/v1/auth/telegram/verify", (req, res) => {
  const configured = (process.env.TELEGRAM_BOT_TOKEN ?? "").trim();
  if (!configured) {
    res.status(503).json({ error: "Telegram authentication is not configured" });
    return;
  }
  try {
    const user = validateInitData(String(req.body?.init_data ?? ""), configured);
    res.json({
      verified: true,
      telegram_user_id: user.id,
      username: user.username,
    });
  } catch {
    res.status(401).json({ error: "Invalid Telegram session" });
  }
});

router.post("/v1/telegram/link", async (req, res): Promise<void> => {
  const user = telegramUser(req, res);
  if (!user) return;
  const fullName = String(req.body?.full_name ?? "").trim();
  const phone = String(req.body?.phone ?? "").trim();
  const email = String(req.body?.email ?? "").trim().toLowerCase() || null;
  if (!fullName || phone.length < 5) {
    res.status(422).json({ error: "Name and phone are required" });
    return;
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const identity = await client.query(
      `SELECT customer_id FROM telegram_identities
       WHERE provider = 'telegram' AND provider_user_id = $1 FOR UPDATE`,
      [user.id],
    );
    const matches = await client.query("SELECT id FROM customers WHERE phone = $1", [
      phone,
    ]);
    if (identity.rowCount) {
      if (!matches.rowCount || matches.rows[0].id !== identity.rows[0].customer_id) {
        await client.query("ROLLBACK");
        res.status(409).json({ error: "Telegram account is already linked" });
        return;
      }
      await client.query("COMMIT");
      res.json({ linked: true, customer_id: identity.rows[0].customer_id });
      return;
    }
    if (matches.rowCount) {
      await client.query("ROLLBACK");
      res.status(409).json({
        error:
          "That phone belongs to an existing customer and requires a verified account recovery flow",
      });
      return;
    }
    const customer = await client.query(
      `INSERT INTO customers (id, full_name, phone, email)
       VALUES (gen_random_uuid(), $1, $2, $3) RETURNING id`,
      [fullName, phone, email],
    );
    const customerId = customer.rows[0].id;
    await client.query(
      `INSERT INTO telegram_identities
       (id, provider, provider_user_id, username, customer_id)
       VALUES (gen_random_uuid(), 'telegram', $1, $2, $3)`,
      [user.id, user.username, customerId],
    );
    await client.query("COMMIT");
    res.json({ linked: true, customer_id: customerId });
  } catch (error) {
    await client.query("ROLLBACK");
    req.log.warn({ error }, "Telegram link conflict");
    res.status(409).json({ error: "Telegram identity or customer is already linked" });
  } finally {
    client.release();
  }
});

router.get("/v1/telegram/cart", async (req, res): Promise<void> => {
  const customer = await linkedCustomer(req, res);
  if (!customer) return;
  res.json(await cartPayload(customer.id));
});

router.post("/v1/telegram/cart/items", async (req, res): Promise<void> => {
  const customer = await linkedCustomer(req, res);
  if (!customer) return;
  const productId = String(req.body?.product_id ?? "");
  const quantity = Number(req.body?.quantity);
  if (!productId || !Number.isInteger(quantity) || quantity < 1 || quantity > 999) {
    res.status(422).json({ error: "Invalid cart line" });
    return;
  }
  const product = await pool.query(
    "SELECT id FROM products WHERE id = $1 AND is_active = true",
    [productId],
  );
  if (!product.rowCount) {
    res.status(404).json({ error: "Product unavailable" });
    return;
  }
  const cartId = await ensureCart(customer.id);
  await pool.query(
    `INSERT INTO cart_items (id, cart_id, product_id, quantity)
     VALUES (gen_random_uuid(), $1, $2, $3)
     ON CONFLICT (cart_id, product_id)
     DO UPDATE SET quantity = EXCLUDED.quantity, updated_at = NOW()`,
    [cartId, productId, quantity],
  );
  res.json(await cartPayload(customer.id));
});

router.delete(
  "/v1/telegram/cart/items/:productId",
  async (req, res): Promise<void> => {
    const customer = await linkedCustomer(req, res);
    if (!customer) return;
    const cartId = await ensureCart(customer.id);
    await pool.query(
      "DELETE FROM cart_items WHERE cart_id = $1 AND product_id = $2",
      [cartId, String(req.params.productId)],
    );
    res.json(await cartPayload(customer.id));
  },
);

router.post("/v1/telegram/cart/checkout", async (req, res): Promise<void> => {
  const customer = await linkedCustomer(req, res);
  if (!customer) return;
  const key = (req.header("x-checkout-idempotency-key") ?? "").trim();
  if (key.length > 128) {
    res.status(400).json({ error: "Invalid checkout idempotency key" });
    return;
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const cartResult = await client.query(
      "SELECT * FROM carts WHERE customer_id = $1 FOR UPDATE",
      [customer.id],
    );
    if (!cartResult.rowCount) {
      await client.query("ROLLBACK");
      res.status(400).json({ error: "Cart is empty" });
      return;
    }
    const cart = cartResult.rows[0];
    if (key && cart.last_checkout_key === key && cart.last_order_id) {
      await client.query("COMMIT");
      const existing = await orderPayload(cart.last_order_id, customer.id);
      res.status(201).json(existing);
      return;
    }
    const lines = await client.query(
      `SELECT ci.product_id, ci.quantity, p.name, p.sku, p.price,
              i.id AS inventory_id, i.quantity AS stock
       FROM cart_items ci
       JOIN products p ON p.id = ci.product_id AND p.is_active = true
       JOIN inventory_items i ON i.product_id = p.id
       WHERE ci.cart_id = $1 FOR UPDATE OF i`,
      [cart.id],
    );
    if (!lines.rowCount) {
      await client.query("ROLLBACK");
      res.status(400).json({ error: "Cart is empty" });
      return;
    }
    let total = 0;
    for (const line of lines.rows) {
      if (Number(line.stock) < Number(line.quantity)) {
        await client.query("ROLLBACK");
        res.status(409).json({ error: "Insufficient stock" });
        return;
      }
      await client.query(
        "UPDATE inventory_items SET quantity = quantity - $1, updated_at = NOW() WHERE id = $2",
        [line.quantity, line.inventory_id],
      );
      total += Number(line.price) * Number(line.quantity);
    }
    const order = await client.query(
      `INSERT INTO orders
       (id, customer_id, customer_name, customer_phone, status, total)
       VALUES (gen_random_uuid(), $1, $2, $3, 'pending', $4)
       RETURNING id`,
      [customer.id, customer.fullName, customer.phone, total.toFixed(2)],
    );
    for (const line of lines.rows) {
      await client.query(
        `INSERT INTO order_items
         (id, order_id, product_id, quantity, unit_price)
         VALUES (gen_random_uuid(), $1, $2, $3, $4)`,
        [order.rows[0].id, line.product_id, line.quantity, line.price],
      );
    }
    await client.query("DELETE FROM cart_items WHERE cart_id = $1", [cart.id]);
    await client.query(
      `UPDATE carts SET last_checkout_key = $1, last_order_id = $2, updated_at = NOW()
       WHERE id = $3`,
      [key || null, order.rows[0].id, cart.id],
    );
    await client.query("COMMIT");
    const payload = await orderPayload(order.rows[0].id, customer.id);
    res.status(201).json(payload);
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
});

router.get("/v1/telegram/orders", async (req, res): Promise<void> => {
  const customer = await linkedCustomer(req, res);
  if (!customer) return;
  const offset = Math.max(0, Number(req.query.offset) || 0);
  const limit = Math.min(100, Math.max(1, Number(req.query.limit) || 50));
  const orders = await pool.query(
    `SELECT id FROM orders WHERE customer_id = $1
     ORDER BY created_at DESC OFFSET $2 LIMIT $3`,
    [customer.id, offset, limit],
  );
  const payloads = await Promise.all(
    orders.rows.map((row) => orderPayload(row.id, customer.id)),
  );
  res.json(payloads.filter(Boolean));
});

router.get("/v1/telegram/orders/:orderId", async (req, res): Promise<void> => {
  const customer = await linkedCustomer(req, res);
  if (!customer) return;
  const payload = await orderPayload(String(req.params.orderId), customer.id);
  if (!payload) {
    res.status(404).json({ error: "Order not found" });
    return;
  }
  res.json(payload);
});

export default router;