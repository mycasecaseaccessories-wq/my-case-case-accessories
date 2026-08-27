import {
  pgTable,
  uuid,
  varchar,
  integer,
  timestamp,
  unique,
} from "drizzle-orm/pg-core";
import { customersTable } from "./customers";
import { productsTable } from "./products";
import { ordersTable } from "./orders";

export const telegramIdentitiesTable = pgTable(
  "telegram_identities",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    provider: varchar("provider", { length: 40 }).notNull().default("telegram"),
    providerUserId: varchar("provider_user_id", { length: 64 }).notNull(),
    username: varchar("username", { length: 255 }),
    customerId: uuid("customer_id")
      .notNull()
      .unique()
      .references(() => customersTable.id, { onDelete: "cascade" }),
    linkedAt: timestamp("linked_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow()
      .$onUpdate(() => new Date()),
  },
  (table) => [
    unique("uq_external_identity_provider_user").on(
      table.provider,
      table.providerUserId,
    ),
  ],
);

export const cartsTable = pgTable("carts", {
  id: uuid("id").primaryKey().defaultRandom(),
  customerId: uuid("customer_id")
    .notNull()
    .unique()
    .references(() => customersTable.id, { onDelete: "cascade" }),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow()
    .$onUpdate(() => new Date()),
  lastCheckoutKey: varchar("last_checkout_key", { length: 128 }).unique(),
  lastOrderId: uuid("last_order_id").references(() => ordersTable.id, {
    onDelete: "set null",
  }),
});

export const cartItemsTable = pgTable(
  "cart_items",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    cartId: uuid("cart_id")
      .notNull()
      .references(() => cartsTable.id, { onDelete: "cascade" }),
    productId: uuid("product_id")
      .notNull()
      .references(() => productsTable.id, { onDelete: "restrict" }),
    quantity: integer("quantity").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow()
      .$onUpdate(() => new Date()),
  },
  (table) => [
    unique("uq_cart_items_cart_product").on(table.cartId, table.productId),
  ],
);