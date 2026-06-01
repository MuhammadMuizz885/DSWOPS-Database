"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "https://dswops-production.up.railway.app";

function getUser() {
  try { return JSON.parse(localStorage.getItem("dswops_user")); } catch { return null; }
}
function getToken() { return localStorage.getItem("dswops_token") || ""; }

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);

  useEffect(() => {
    const u = getUser();
    if (!u) { router.push("/"); return; }
    setUser(u);
    fetchStats(u);
  }, []);

  async function fetchStats(u) {
    const token = getToken();
    try {
      if (u.role === "admin") {
        const r = await fetch(`${API}/api/admin/stats`, { headers: { "X-Auth-Token": token } });
        const d = await r.json();
        setStats(d);
        setActivity(d.recent_activity || []);
      } else {
        const r = await fetch(`${API}/api/documents?limit=5`, { headers: { "X-Auth-Token": token } });
        const d = await r.json();
        setStats({ total: d.total || 0 });
      }
    } catch {}
  }

  const logout = async () => {
    await fetch(`${API}/api/auth/logout`, { method: "POST", headers: { "X-Auth-Token": getToken() } }).catch(() => {});
    localStorage.removeItem("dswops_token");
    localStorage.removeItem("dswops_user");
    router.push("/");
  };

  if (!user) return <div className="loading-center"><div className="spinner" /> Loading…</div>;

  return (
    <div className="shell">
      <Sidebar user={user} active="dashboard" onLogout={logout} />
      <main className="main">
        <div className="page-title">Welcome back, {user.display_name} 👋</div>
        <div className="page-sub">Here's what's happening in DSWOPS today.</div>

        {stats && (
          <div className="stat-grid">
            <StatCard label="Total Documents" value={stats.total ?? "—"} sub="all time" />
            {stats.completed !== undefined && <StatCard label="Completed" value={stats.completed} sub={`${stats.success_rate}% success`} color="var(--success)" />}
            {stats.failed    !== undefined && <StatCard label="Failed"    value={stats.failed}    sub="need attention"  color="var(--danger)"  />}
            {stats.letters   !== undefined && <StatCard label="Letters"   value={stats.letters}   sub="documents"       color="var(--accent)"  />}
            {stats.office_orders !== undefined && <StatCard label="Office Orders" value={stats.office_orders} sub="documents" color="#a78bfa" />}
            {stats.active_users  !== undefined && <StatCard label="Active Users"  value={stats.active_users}  sub={`of ${stats.total_users} total`} />}
          </div>
        )}

        {activity.length > 0 && (
          <div className="card">
            <div className="section-label" style={{marginBottom:16}}>Recent Activity</div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Action</th><th>File</th><th>Role</th><th>Time</th></tr></thead>
                <tbody>
                  {activity.slice(0,10).map((a, i) => (
                    <tr key={i}>
                      <td><span className="tag tag-pending">{a.action}</span></td>
                      <td style={{maxWidth:200,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{a.filename || "—"}</td>
                      <td style={{color:"var(--muted)"}}>{a.role}</td>
                      <td style={{color:"var(--muted)"}}>{a.timestamp ? new Date(a.timestamp).toLocaleString() : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!stats && <div className="card"><div style={{color:"var(--muted)",fontSize:14}}>Use the sidebar to scan documents, view records, or manage users.</div></div>}
      </main>
    </div>
  );
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={color ? { color } : {}}>{value}</div>
      <div className="stat-sub">{sub}</div>
    </div>
  );
}

export function Sidebar({ user, active, onLogout }) {
  const initials = (user?.display_name || "U").split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase();
  const isAdmin = user?.role === "admin";
  const nav = [
    { id: "dashboard", label: "Dashboard",     icon: "⊞", href: "/dashboard" },
    { id: "scan",      label: "Scan Document",  icon: "⬆", href: "/scan"      },
    { id: "records",   label: "Records",        icon: "☰", href: "/records"   },
    { id: "activity",  label: "Activity Log",   icon: "◷", href: "/activity"  },
    ...(isAdmin ? [{ id: "admin", label: "Admin Panel", icon: "⚙", href: "/admin" }] : []),
  ];
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-name">DSWOPS</div>
        <div className="sidebar-brand-sub">Wildlife Directorate KP</div>
      </div>
      <nav className="sidebar-nav">
        {nav.map(n => (
          <Link key={n.id} href={n.href} className={`nav-item${active === n.id ? " active" : ""}`}>
            <span className="nav-icon">{n.icon}</span>{n.label}
          </Link>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="user-chip">
          <div className="user-avatar">{initials}</div>
          <div><div className="user-name">{user?.display_name}</div><div className="user-role">{user?.role}</div></div>
        </div>
        <button className="btn-logout" onClick={onLogout}>Sign Out</button>
      </div>
    </aside>
  );
}