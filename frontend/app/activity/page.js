"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "../dashboard/page";

const API = process.env.NEXT_PUBLIC_API_URL || "https://dswops-production.up.railway.app";
const getToken = () => localStorage.getItem("dswops_token") || "";
const getUser  = () => { try { return JSON.parse(localStorage.getItem("dswops_user")); } catch { return null; } };

export default function ActivityPage() {
  const router = useRouter();
  const [user, setUser]   = useState(null);
  const [logs, setLogs]   = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const u = getUser(); if (!u) { router.push("/"); return; } setUser(u);
    fetchData(u);
  }, []);

  async function fetchData(u) {
    setLoading(true);
    const h = { "X-Auth-Token": getToken() };
    try {
      const [lr, sr] = await Promise.all([
        fetch(`${API}/api/audit-logs?limit=50`, { headers: h }),
        fetch(`${API}/api/documents?limit=1`,   { headers: h }),
      ]);
      const ld = await lr.json(); setLogs(ld.logs || ld || []);
      const sd = await sr.json(); setStats({ total: sd.total || 0 });
    } catch {}
    finally { setLoading(false); }
  }

  const logout = async () => {
    await fetch(`${API}/api/auth/logout`,{method:"POST",headers:{"X-Auth-Token":getToken()}}).catch(()=>{});
    localStorage.clear(); router.push("/");
  };

  const actionColor = a => ({ upload:"tag-pending", extract:"tag-letter", save:"tag-done", delete:"tag-failed" }[a] || "tag-pending");

  if (!user) return <div className="loading-center"><div className="spinner"/>Loading…</div>;

  return (
    <div className="shell">
      <Sidebar user={user} active="activity" onLogout={logout}/>
      <main className="main">
        <div className="page-title">Activity Log</div>
        <div className="page-sub">Your recent document processing history.</div>
        {stats && (
          <div className="stat-grid" style={{marginBottom:24}}>
            <div className="stat-card"><div className="stat-label">Total Docs</div><div className="stat-value">{stats.total}</div></div>
          </div>
        )}
        <div className="card">
          {loading ? (
            <div className="loading-center"><div className="spinner"/>Loading logs…</div>
          ) : logs.length === 0 ? (
            <div style={{color:"var(--muted)",textAlign:"center",padding:"40px",fontSize:14}}>No activity yet.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Action</th><th>File</th><th>Time</th></tr></thead>
                <tbody>
                  {logs.map((l,i) => (
                    <tr key={i}>
                      <td><span className={`tag ${actionColor(l.action)}`}>{l.action}</span></td>
                      <td style={{maxWidth:300,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{l.filename||"—"}</td>
                      <td style={{color:"var(--muted)",fontSize:12}}>{l.timestamp ? new Date(l.timestamp).toLocaleString() : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}