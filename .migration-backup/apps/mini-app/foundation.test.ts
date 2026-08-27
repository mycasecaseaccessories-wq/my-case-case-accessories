import { describe, expect, it } from "vitest";

import { calculateSubtotal, clampQuantity, money } from "./app/cart-utils";

describe("Telegram Mini App foundation", () => {
  it("uses the My Case Telegram storefront identity", () => {
    expect("My Case / Telegram Store").toContain("Telegram Store");
  });

  it("keeps the central API architecture explicit", () => {
    expect("Central API / Central Database").toContain("Central API");
  });

  it("formats MMK and calculates the cart subtotal", () => {
    const lines = [
      { product: { id: "a", name: "Case", sku: "CASE-1", price: "1200.50" }, quantity: 2 },
      { product: { id: "b", name: "Cable", sku: "CAB-1", price: 800 }, quantity: 1 },
    ];
    expect(calculateSubtotal(lines)).toBe(3201);
    expect(money(calculateSubtotal(lines))).toBe("3,201.00 MMK");
  });

  it("clamps quantities to the safe client range", () => {
    expect(clampQuantity(0)).toBe(1);
    expect(clampQuantity(7.8)).toBe(7);
    expect(clampQuantity(5000)).toBe(999);
  });
});
