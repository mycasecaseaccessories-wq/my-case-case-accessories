"use client";

import { FormEvent, useEffect, useState } from "react";

type Category = { id: string; name: string; slug: string; description?: string | null; is_active: boolean };
type Product = {
  id: string;
  category_id: string;
  name: string;
  slug: string;
  sku: string;
  price: string;
  is_active: boolean;
};

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function CatalogPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [categoryName, setCategoryName] = useState("");
  const [categorySlug, setCategorySlug] = useState("");
  const [productName, setProductName] = useState("");
  const [productSlug, setProductSlug] = useState("");
  const [productSku, setProductSku] = useState("");
  const [productPrice, setProductPrice] = useState("");
  const [productCategoryId, setProductCategoryId] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const [categoryResponse, productResponse] = await Promise.all([
      fetch(`${API}/catalog/categories`),
      fetch(`${API}/catalog/products`),
    ]);
    if (!categoryResponse.ok || !productResponse.ok) throw new Error("API မရနိုင်ပါ");
    setCategories(await categoryResponse.json());
    setProducts(await productResponse.json());
  }

  useEffect(() => {
    load().catch((error: Error) => setMessage(error.message));
  }, []);

  async function createProduct(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`${API}/catalog/products`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category_id: productCategoryId,
        name: productName,
        slug: productSlug,
        sku: productSku,
        price: productPrice,
      }),
    });
    if (!response.ok) {
      setMessage("Product ထည့်၍မရပါ");
      return;
    }
    setProductName("");
    setProductSlug("");
    setProductSku("");
    setProductPrice("");
    setMessage("Product ထည့်ပြီးပါပြီ");
    await load();
  }

  async function createCategory(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`${API}/catalog/categories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: categoryName, slug: categorySlug }),
    });
    if (!response.ok) {
      setMessage("Category ထည့်၍မရပါ");
      return;
    }
    setCategoryName("");
    setCategorySlug("");
    setMessage("Category ထည့်ပြီးပါပြီ");
    await load();
  }

  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem", maxWidth: 1000, margin: "0 auto" }}>
      <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case v1 · Admin</p>
      <h1>Catalog Management</h1>
      <p>Category များနှင့် product catalog ကို စီမံနိုင်သော Feature 1 screen ဖြစ်သည်။</p>
      {message && <p role="status">{message}</p>}
      <form onSubmit={createCategory} style={{ display: "flex", gap: 8, margin: "24px 0" }}>
        <input
          required
          placeholder="Category name"
          value={categoryName}
          onChange={(e) => setCategoryName(e.target.value)}
        />
        <input
          required
          pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
          placeholder="slug"
          value={categorySlug}
          onChange={(e) => setCategorySlug(e.target.value)}
        />
        <button type="submit">Add category</button>
      </form>
      <section>
        <h2>Categories ({categories.length})</h2>
        <ul>
          {categories.map((category) => (
            <li key={category.id}>
              {category.name} <small>({category.slug})</small>
            </li>
          ))}
        </ul>
      </section>
      <form onSubmit={createProduct} style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "24px 0" }}>
        <input
          required
          placeholder="Product name"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
        />
        <input
          required
          pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
          placeholder="slug"
          value={productSlug}
          onChange={(e) => setProductSlug(e.target.value)}
        />
        <input required placeholder="SKU" value={productSku} onChange={(e) => setProductSku(e.target.value)} />
        <input
          required
          min="0"
          step="0.01"
          type="number"
          placeholder="Price"
          value={productPrice}
          onChange={(e) => setProductPrice(e.target.value)}
        />
        <select required value={productCategoryId} onChange={(e) => setProductCategoryId(e.target.value)}>
          <option value="">Select category</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        <button type="submit">Add product</button>
      </form>
      <section>
        <h2>Products ({products.length})</h2>
        <ul>
          {products.map((product) => (
            <li key={product.id}>
              {product.name} · {product.sku} · {product.price}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
