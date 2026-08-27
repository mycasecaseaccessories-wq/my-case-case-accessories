"use client";

import { useEffect, useMemo, useState } from "react";

type Product = { id: string; name: string; sku: string; price: string };
const API = (import.meta.env.VITE_API_BASE_URL as string) || "/api/v1";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selected, setSelected] = useState<Record<string, number>>({});
  const [query, setQuery] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    fetch(`${API}/catalog/products`)
      .then((response) => response.json())
      .then(setProducts)
      .catch(() => setMessage("Product API မရနိုင်ပါ"));
  }, []);
  const visible = useMemo(
    () => products.filter((product) => `${product.name} ${product.sku}`.toLowerCase().includes(query.toLowerCase())),
    [products, query],
  );
  const total = products.reduce((sum, product) => sum + Number(product.price) * (selected[product.id] || 0), 0);
  async function completeSale() {
    const items = Object.entries(selected)
      .filter(([, quantity]) => quantity > 0)
      .map(([product_id, quantity]) => ({ product_id, quantity }));
    if (!items.length || !customerName || !customerPhone) {
      setMessage("Customer နှင့် product ကို ဖြည့်/ရွေးပါ");
      return;
    }
    let customerResponse = await fetch(`${API}/customers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: customerName, phone: customerPhone }),
    });
    let customer: { id: string } | null = null;
    if (customerResponse.status === 409) {
      customer = null;
    } else {
      if (!customerResponse.ok) {
        setMessage("Customer မသိမ်းနိုင်ပါ");
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
        items,
      }),
    });
    if (!response.ok) {
      setMessage("Sale မပြီးမြောက်ပါ။ Stock ကို စစ်ပါ။");
      return;
    }
    const order = await response.json();
    setSelected({});
    setMessage(`Sale completed · ${order.id} · ${order.total} MMK`);
  }
  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case v1 · POS</p>
      <h1>Point of Sale</h1>
      <input
        aria-label="Search POS products"
        placeholder="Search by name or SKU"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
        <input
          required
          placeholder="Customer name"
          value={customerName}
          onChange={(event) => setCustomerName(event.target.value)}
        />
        <input
          required
          placeholder="Customer phone"
          value={customerPhone}
          onChange={(event) => setCustomerPhone(event.target.value)}
        />
      </div>
      {message && <p role="status">{message}</p>}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 16,
          margin: "24px 0",
        }}
      >
        {visible.map((product) => (
          <article key={product.id} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 16 }}>
            <h2 style={{ fontSize: "1rem" }}>{product.name}</h2>
            <p>
              {product.sku} · {product.price} MMK
            </p>
            <input
              aria-label={`Quantity for ${product.name}`}
              type="number"
              min="0"
              value={selected[product.id] || 0}
              onChange={(event) => setSelected({ ...selected, [product.id]: Number(event.target.value) })}
            />
          </article>
        ))}
      </section>
      <h2>Total: {total.toFixed(2)} MMK</h2>
      <button type="button" onClick={completeSale}>
        Complete sale
      </button>
    </main>
  );
}
