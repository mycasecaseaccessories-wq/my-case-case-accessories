"use client";

import { useEffect, useMemo, useState } from "react";

type Category = { id: string; name: string; slug: string };
type Product = {
  id: string;
  category_id: string;
  name: string;
  slug: string;
  sku: string;
  description?: string | null;
  price: string;
};
type CartLine = { product: Product; quantity: number };
const API = (import.meta.env.VITE_API_BASE_URL as string) || "/api/v1";

export default function Home() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [showCart, setShowCart] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [orderMessage, setOrderMessage] = useState("");

  useEffect(() => {
    const saved = window.localStorage.getItem("mycase-cart");
    if (saved) setCart(JSON.parse(saved));
    Promise.all([fetch(`${API}/catalog/categories`), fetch(`${API}/catalog/products`)])
      .then(async ([categoryResponse, productResponse]) => {
        if (!categoryResponse.ok || !productResponse.ok) throw new Error("Catalog မရနိုင်ပါ");
        setCategories(await categoryResponse.json());
        setProducts(await productResponse.json());
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    window.localStorage.setItem("mycase-cart", JSON.stringify(cart));
  }, [cart]);

  const addToCart = (product: Product) =>
    setCart((current) => {
      const found = current.find((line) => line.product.id === product.id);
      return found
        ? current.map((line) => (line.product.id === product.id ? { ...line, quantity: line.quantity + 1 } : line))
        : [...current, { product, quantity: 1 }];
    });
  const changeQuantity = (productId: string, quantity: number) =>
    setCart((current) =>
      quantity > 0
        ? current.map((line) => (line.product.id === productId ? { ...line, quantity } : line))
        : current.filter((line) => line.product.id !== productId),
    );
  const cartTotal = cart.reduce((sum, line) => sum + Number(line.product.price) * line.quantity, 0);

  async function checkout() {
    let customerResponse = await fetch(`${API}/customers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: customerName, phone: customerPhone }),
    });
    let customer: { id: string } | null = null;
    if (customerResponse.status === 409) {
      // Existing identities are not exposed to an unauthenticated checkout.
      // The order keeps its customer snapshot without attaching account history.
      customer = null;
    } else {
      if (!customerResponse.ok) {
        setOrderMessage("Customer information မသိမ်းနိုင်ပါ။");
        return;
      }
      customer = await customerResponse.json();
    }
    const response = await fetch(`${API}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: customer?.id,
        customer_name: customerName,
        customer_phone: customerPhone,
        items: cart.map((line) => ({ product_id: line.product.id, quantity: line.quantity })),
      }),
    });
    if (!response.ok) {
      setOrderMessage("Order မတင်နိုင်ပါ။ Stock နှင့် customer information ကို စစ်ပါ။");
      return;
    }
    const order = await response.json();
    setOrderMessage(`Order တင်ပြီးပါပြီ။ Order ID: ${order.id}`);
    setCart([]);
    setCustomerName("");
    setCustomerPhone("");
  }

  const visibleProducts = useMemo(
    () =>
      products.filter((product) => {
        const matchesCategory = !selectedCategory || product.category_id === selectedCategory;
        const haystack = `${product.name} ${product.sku} ${product.description || ""}`.toLowerCase();
        return matchesCategory && haystack.includes(query.toLowerCase());
      }),
    [products, query, selectedCategory],
  );

  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <header
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, flexWrap: "wrap" }}
      >
        <div>
          <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case</p>
          <h1>Case Accessories</h1>
          <p>သင့်ဖုန်းအတွက် လိုအပ်သမျှ accessory များကို ရှာဖွေပါ။</p>
        </div>
        <button type="button" onClick={() => setShowCart(!showCart)}>
          Cart ({cart.reduce((sum, line) => sum + line.quantity, 0)})
        </button>
      </header>
      <section style={{ display: "flex", gap: 8, margin: "24px 0", flexWrap: "wrap" }}>
        <input
          aria-label="Search products"
          placeholder="Search products"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <select
          aria-label="Filter by category"
          value={selectedCategory}
          onChange={(event) => setSelectedCategory(event.target.value)}
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </section>
      {error && <p role="alert">{error}</p>}
      {showCart && (
        <aside style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 16, marginBottom: 24 }}>
          <h2>Cart</h2>
          {cart.length === 0 ? (
            <p>Cart empty</p>
          ) : (
            <>
              {cart.map((line) => (
                <p key={line.product.id}>
                  {line.product.name}{" "}
                  <input
                    aria-label={`Quantity for ${line.product.name}`}
                    type="number"
                    min="0"
                    value={line.quantity}
                    onChange={(event) => changeQuantity(line.product.id, Number(event.target.value))}
                  />{" "}
                  × {line.product.price}
                </p>
              ))}
              <strong>Total: {cartTotal.toFixed(2)} MMK</strong>
              <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                <input
                  required
                  placeholder="Customer name"
                  value={customerName}
                  onChange={(event) => setCustomerName(event.target.value)}
                />
                <input
                  required
                  placeholder="Phone"
                  value={customerPhone}
                  onChange={(event) => setCustomerPhone(event.target.value)}
                />
                <button
                  type="button"
                  onClick={checkout}
                  disabled={!customerName || !customerPhone || cart.length === 0}
                >
                  Checkout
                </button>
              </div>
            </>
          )}
          {orderMessage && <p role="status">{orderMessage}</p>}
        </aside>
      )}
      {!error && visibleProducts.length === 0 && <p>Product မတွေ့သေးပါ။</p>}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        {visibleProducts.map((product) => (
          <article key={product.id} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 16 }}>
            <h2 style={{ fontSize: "1.1rem" }}>{product.name}</h2>
            <p>{product.description || "Quality accessory"}</p>
            <strong>{product.price} MMK</strong>
            <p>
              <small>SKU: {product.sku}</small>
            </p>
            <button type="button" onClick={() => addToCart(product)}>
              Add to cart
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}
