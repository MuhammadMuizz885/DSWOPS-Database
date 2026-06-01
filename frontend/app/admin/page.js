"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "../dashboard/page";

const API = "http://localhost:8000";
const getToken = () => localStorage.getItem("dswops_token") || "";
const getUser  = () => { try { return JSON.parse(localStorage.getItem("dswops_user")); } catch { return null; } };

const ALL_ROLES = ["admin", "manager", "officer", "viewer"];

export default function AdminPage() {
  const router = useRouter();
  const [user, setUser]   = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // null | {mode:"create"|"edit", data?}
  const [form, setForm]   = useState({ username:"", password:"", role:"director", display_name:"", is_active:true });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg]     = useState("");

  useEffect(() => {
    const u = getUser();
    if (!u || u.role !== "admin") { router.push("/dashboard"); return; }
    setUser(u); fetchUsers();
  }, []);

  async function fetchUsers() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/admin/users`, { headers:{"X-Auth-Token":getToken()} });
      const d = await r.json(); setUsers(d);
    } catch {}
    finally { setLoading(false); }
  }

  function openCreate() {
    setForm({ username:"", password:"", role:"director", display_name:"", is_active:true });
    setMsg(""); setModal({ mode:"create" });
  }

  function openEdit(u) {
    setForm({ username:u.username, password:"", role:u.role, display_name:u.display_name||"", is_active:u.is_active });
    setMsg(""); setModal({ mode:"edit", id:u.id });
  }

  async function handleSave() {
    setSaving(true); setMsg("");
    try {
      const isCreate = modal.mode === "create";
      const url = isCreate ? `${API}/api/admin/users` : `${API}/api/admin/users/${modal.id}`;
      const body = isCreate ? form : { ...form, ...(form.password ? {} : { password: undefined }) };
      const r = await fetch(url, {
        method: isCreate ? "POST" : "PUT",
        headers: {"Content-Type":"application/json","X-Auth-Token":getToken()},
        body: JSON.stringify(body),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Failed");
      setModal(null); fetchUsers();
    } catch(e) { setMsg(e.message); }
    finally { setSaving(false); }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this user?")) return;
    await fetch(`${API}/api/admin/users/${id}`, { method:"DELETE", headers:{"X-Auth-Token":getToken()} });
    fetchUsers();
  }

  const logout = async () => {
    await fetch(`${API}/api/auth/logout`,{method:"POST",headers:{"X-Auth-Token":getToken()}}).catch(()=>{});
    localStorage.clear(); router.push("/");
  };

  if (!user) return <div className="loading-center"><div className="spinner"/>Loading…</div>;

  return (
    <div className="shell">
      <Sidebar user={user} active="admin" onLogout={logout}/>
      <main className="main">
        <div className="page-title">Admin Panel</div>
        <div className="page-sub">Manage user accounts and system access.</div>

        <div style={{marginBottom:20}}>
          <button className="btn-primary" style={{width:"auto",padding:"10px 24px"}} onClick={openCreate}>
            + Create User
          </button>
        </div>

        <div className="card">
          {loading ? (
            <div className="loading-center"><div className="spinner"/>Loading users…</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Username</th><th>Display Name</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td style={{fontWeight:600}}>{u.username}</td>
                      <td>{u.display_name||"—"}</td>
                      <td><span className="tag tag-letter">{u.role}</span></td>
                      <td>
                        <span className={`tag ${u.is_active?"tag-done":"tag-failed"}`}>
                          {u.is_active?"Active":"Inactive"}
                        </span>
                      </td>
                      <td>
                        <div style={{display:"flex",gap:8}}>
                          <button className="btn-secondary" style={{padding:"5px 12px",fontSize:12}} onClick={()=>openEdit(u)}>Edit</button>
                          {u.id !== user.user_id && (
                            <button className="btn-danger" onClick={()=>handleDelete(u.id)}>Delete</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {modal && (
          <div className="modal-overlay" onClick={e=>e.target===e.currentTarget&&setModal(null)}>
            <div className="modal">
              <div className="modal-title">{modal.mode==="create"?"Create User":"Edit User"}</div>
              {modal.mode==="create" && (
                <>
                  <label className="field-label">Username</label>
                  <input className="field-input" value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/>
                </>
              )}
              <label className="field-label">Display Name</label>
              <input className="field-input" value={form.display_name} onChange={e=>setForm({...form,display_name:e.target.value})}/>
              <label className="field-label">Role</label>
              <select className="field-input" value={form.role} onChange={e=>setForm({...form,role:e.target.value})}>
                {ALL_ROLES.map(r=><option key={r} value={r}>{r}</option>)}
              </select>
              <label className="field-label">{modal.mode==="edit"?"New Password (leave blank to keep)":"Password"}</label>
              <input className="field-input" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
              {modal.mode==="edit" && (
                <>
                  <label className="field-label">Status</label>
                  <select className="field-input" value={form.is_active?"active":"inactive"} onChange={e=>setForm({...form,is_active:e.target.value==="active"})}>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </>
              )}
              {msg && <div className="msg-error">{msg}</div>}
              <div className="modal-actions">
                <button className="btn-secondary" onClick={()=>setModal(null)}>Cancel</button>
                <button className="btn-primary" style={{width:"auto",padding:"10px 24px"}} onClick={handleSave} disabled={saving}>
                  {saving?"Saving…":"Save"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}