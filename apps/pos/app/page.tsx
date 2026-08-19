export default function Home() {
  return (
    <main style={{ fontFamily: "system-ui", padding: "3rem", maxWidth: 720, margin: "0 auto" }}>
      <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case v1</p>
      <h1>POS foundation</h1>
      <p>
        This is the B00 online-first POS shell. Sales, shifts, payments, barcode scanning, receipts, returns, and
        offline synchronization are intentionally not implemented.
      </p>
      <p>API base: {process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"}</p>
    </main>
  );
}
