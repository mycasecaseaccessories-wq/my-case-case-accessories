"use client";

import { useEffect, useMemo, useState } from "react";

type Product = { id: string; name: string; price: string };
type Inventory = { product_id: string; quantity: number; reorder_level: number; low_stock: boolean };
type Order = { id: string; status: string; total: string };
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const authHeaders = () => ({ Authorization: `Bearer ${window.localStorage.getItem("mycase-access-token") || ""}` });

export default function DashboardPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([
      fetch(`${API}/catalog/products`),
      fetch(`${API}/inventory`, { headers: authHeaders() }),
      fetch(`${API}/orders`, { headers: authHeaders() }),
    ])
      .then(async ([p, i, o]) => {
        if (!p.ok || !i.ok || !o.ok) throw new Error("Dashboard API မရနိုင်ပါ");
        setProducts(await p.json());
        setInventory(await i.json());
        setOrders(await o.json());
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);
  const revenue = useMemo(() => orders.reduce((sum, order) => sum + Number(order.total), 0), [orders]);
  const lowStock = inventory.filter((item) => item.low_stock).length;
  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case v1 · Admin</p>
      <h1>Operations Dashboard</h1>
      {error && <p role="alert">{error}</p>}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16,
          margin: "24px 0",
        }}
      >
        {[
          ["Products", products.length],
          ["Inventory items", inventory.length],
          ["Low stock", lowStock],
          ["Orders", orders.length],
          ["Order total", `${revenue.toFixed(2)} MMK`],
        ].map(([label, value]) => (
          <article key={String(label)} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 16 }}>
            <small>{label}</small>
            <h2>{value}</h2>
          </article>
        ))}
      </section>
      <h2>Recent orders</h2>
      <ul>
        {orders.slice(0, 10).map((order) => (
          <li key={order.id}>
            {order.id} · {order.status} · {order.total} MMK
          </li>
        ))}
      </ul>
    </main>
  );
}
