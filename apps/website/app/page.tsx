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
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function Home() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([fetch(`${API}/catalog/categories`), fetch(`${API}/catalog/products`)])
      .then(async ([categoryResponse, productResponse]) => {
        if (!categoryResponse.ok || !productResponse.ok) throw new Error("Catalog မရနိုင်ပါ");
        setCategories(await categoryResponse.json());
        setProducts(await productResponse.json());
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

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
        <button type="button" onClick={() => alert("Cart feature ကို နောက်အဆင့်တွင် ထည့်သွင်းမည်။")}>
          Cart (0)
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
            <button type="button" onClick={() => alert("Cart feature ကို နောက်အဆင့်တွင် ထည့်သွင်းမည်။")}>
              Add to cart
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}
