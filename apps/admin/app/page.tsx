export default function Home() {
  return (
    <main style={{ fontFamily: "system-ui", padding: "3rem", maxWidth: 720, margin: "0 auto" }}>
      <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case v1</p>
      <h1>Admin foundation</h1>
      <p>
        Catalog management ကို စတင်အသုံးပြုနိုင်ပါပြီ။ Inventory, orders, payments နှင့် operational dashboard များကို
        နောက်အဆင့်များတွင် ထည့်သွင်းမည်။
      </p>
      <p>API base: {process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"}</p>
      <p>
        <a href="/catalog">Catalog Management →</a>
      </p>
    </main>
  );
}
