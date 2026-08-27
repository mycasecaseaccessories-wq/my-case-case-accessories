import { pgTable, uuid, integer, varchar, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";
import { productsTable } from "./products";

export const inventoryItemsTable = pgTable("inventory_items", {
  id: uuid("id").primaryKey().defaultRandom(),
  productId: uuid("product_id")
    .notNull()
    .unique()
    .references(() => productsTable.id, { onDelete: "cascade" }),
  quantity: integer("quantity").notNull().default(0),
  reorderLevel: integer("reorder_level").notNull().default(5),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow()
    .$onUpdate(() => new Date()),
});

export const stockMovementsTable = pgTable("stock_movements", {
  id: uuid("id").primaryKey().defaultRandom(),
  inventoryId: uuid("inventory_id")
    .notNull()
    .references(() => inventoryItemsTable.id, { onDelete: "cascade" }),
  delta: integer("delta").notNull(),
  reason: varchar("reason", { length: 120 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const insertInventoryItemSchema = createInsertSchema(inventoryItemsTable).omit({
  id: true,
  updatedAt: true,
});
export type InsertInventoryItem = z.infer<typeof insertInventoryItemSchema>;
export type InventoryItem = typeof inventoryItemsTable.$inferSelect;
export type StockMovement = typeof stockMovementsTable.$inferSelect;
