export type CartProduct = { price: string | number };
export type CartLine = { product: CartProduct; quantity: number };

export function money(value: string | number) {
  return `${Number(value).toLocaleString("en-US", { minimumFractionDigits: 2 })} MMK`;
}

export function calculateSubtotal(lines: CartLine[]) {
  return lines.reduce((sum, line) => sum + Number(line.product.price) * line.quantity, 0);
}

export function clampQuantity(quantity: number) {
  return Math.max(1, Math.min(999, Math.trunc(quantity)));
}
