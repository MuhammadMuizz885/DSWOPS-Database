"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("dswops_token");
    if (token) router.push("/dashboard");
  }, []);

  const handleLogin = async () => {
    if (!username || !password) { setMessage("Enter username and password"); return; }
    setLoading(true); setMessage("");
    try {
      const res = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) { setMessage(data.detail || "Login failed"); return; }
      localStorage.setItem("dswops_token", data.token);
      localStorage.setItem("dswops_user", JSON.stringify(data));
      router.push("/dashboard");
    } catch { setMessage("Cannot reach server — is the backend running?"); }
    finally { setLoading(false); }
  };

  const onKey = (e) => { if (e.key === "Enter") handleLogin(); };

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-logo">DSWOPS</div>
        <div className="login-sub">Document Scanner & Work Order Processing System<br/>Directorate of Wildlife, KP</div>
        <label className="field-label">Username</label>
        <input className="field-input" value={username} onChange={e => setUsername(e.target.value)} onKeyDown={onKey} autoFocus />
        <label className="field-label">Password</label>
        <input className="field-input" type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={onKey} />
        <button className="btn-primary" onClick={handleLogin} disabled={loading}>
          {loading ? "Signing in…" : "Sign In"}
        </button>
            <p style={{ textAlign: "center", fontSize: 14, color: "#7a849e" }}>
              New office?{" "}
            <a href="/register" style={{ color: "#4f6ef7", fontWeight: 500 }}>
              Register here
            </a>
            </p>
        {message && <div className="msg-error">{message}</div>}
      </div>
    </div>
  );
}
