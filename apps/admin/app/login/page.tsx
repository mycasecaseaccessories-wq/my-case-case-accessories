"use client";

import { FormEvent, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  async function login(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      setMessage("Login မအောင်မြင်ပါ");
      return;
    }
    const data = await response.json();
    window.localStorage.setItem("mycase-access-token", data.access_token);
    setMessage(`Login အောင်မြင်ပါပြီ။ Role: ${data.user.role}`);
  }
  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem", maxWidth: 520, margin: "0 auto" }}>
      <p style={{ color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>My Case v1 · Admin</p>
      <h1>Sign in</h1>
      <form onSubmit={login} style={{ display: "grid", gap: 12 }}>
        <input
          required
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <input
          required
          minLength={8}
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <button type="submit">Login</button>
      </form>
      {message && <p role="status">{message}</p>}
    </main>
  );
}
