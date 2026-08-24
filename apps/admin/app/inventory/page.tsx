"use client";

import { FormEvent, useEffect, useState } from "react";

type Item = { product_id: string; quantity: number; reorder_level: number; low_stock: boolean };
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function InventoryPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [productId, setProductId] = useState("");
  const [delta, setDelta] = useState("1");
  const [reason, setReason] = useState("manual adjustment");
  const [message, setMessage] = useState("");

  async function load() {
    const response = await fetch(`${API}/inventory`);
    if (!response.ok) throw new Error("Inventory API မရနိုင်ပါ");
    setItems(await response.json());
  }
  useEffect(() => {
    load().catch((error: Error) => setMessage(error.message));
  }, []);

  async function adjust(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`${API}/inventory/${productId}/adjust`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ delta: Number(delta), reason }),
    });
    if (!response.ok) {
      setMessage("Stock ပြောင်း၍မရပါ");
      return;
    }
    setMessage("Stock update ပြီးပါပြီ");
    setProductId("");
    await load();
  }

  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem", maxWidth: 1000, margin: "0 auto" }}>
      <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case v1 · Admin</p>
      <h1>Inventory Management</h1>
      <p>Product ID ဖြင့် stock လက်ခံခြင်း သို့မဟုတ် လျှော့ချခြင်းကို မှတ်တမ်းတင်နိုင်ပါသည်။</p>
      {message && <p role="status">{message}</p>}
      <form onSubmit={adjust} style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "24px 0" }}>
        <input required placeholder="Product UUID" value={productId} onChange={(e) => setProductId(e.target.value)} />
        <input
          required
          type="number"
          step="1"
          placeholder="+/- quantity"
          value={delta}
          onChange={(e) => setDelta(e.target.value)}
        />
        <input required placeholder="Reason" value={reason} onChange={(e) => setReason(e.target.value)} />
        <button type="submit">Update stock</button>
      </form>
      <h2>Stock items ({items.length})</h2>
      <ul>
        {items.map((item) => (
          <li key={item.product_id}>
            {item.product_id} · {item.quantity} units {item.low_stock ? "· LOW STOCK" : ""}
          </li>
        ))}
      </ul>
    </main>
  );
}
