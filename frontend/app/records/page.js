"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "../dashboard/page";

const API = "http://localhost:8000";
const getToken = () => localStorage.getItem("dswops_token") || "";
const getUser  = () => { try { return JSON.parse(localStorage.getItem("dswops_user")); } catch { return null; } };

const FIELD_LABELS = {
  doc_number: "Doc / Ref No.",
  date:       "Date",
  subject:    "Subject",
  from_field: "From",
  to_field:   "To",
  ccwl_no:    "CCWL",
  notes:      "Notes",
};

export default function RecordsPage() {
  const router = useRouter();
  const [user, setUser]       = useState(null);
  const [records, setRecords] = useState([]);
  const [total, setTotal]     = useState(0);
  const [pages, setPages]     = useState(1);
  const [page, setPage]       = useState(1);
  const [loading, setLoading] = useState(true);

  // Detail modal
  const [detail, setDetail]       = useState(null);
  const [detailLoading, setDL]    = useState(false);

  // Delete confirm
  const [deleting, setDeleting]   = useState(null); // record id pending confirm
  const [deleteWorking, setDW]    = useState(false);

  useEffect(() => {
    const u = getUser(); if (!u) { router.push("/"); return; } setUser(u);
    fetchRecords(1, u);
  }, []);

  async function fetchRecords(p, u) {
    setLoading(true);
    const endpoint = (u || user)?.role === "admin"
      ? `${API}/api/admin/records?page=${p}&limit=20`
      : `${API}/api/documents?page=${p}&limit=20`;
    try {
      const r = await fetch(endpoint, { headers: { "X-Auth-Token": getToken() } });
      const d = await r.json();
      setRecords(d.records || d.documents || []);
      setTotal(d.total || 0);
      setPages(d.pages || 1);
      setPage(p);
    } catch {}
    finally { setLoading(false); }
  }

  async function openDetail(id) {
    setDL(true);
    setDetail({ loading: true });
    try {
      const r = await fetch(`${API}/api/document/${id}`, { headers: { "X-Auth-Token": getToken() } });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Failed to load");
      setDetail(d);
    } catch (e) {
      setDetail({ error: e.message });
    } finally { setDL(false); }
  }

  async function confirmDelete() {
    if (!deleting) return;
    setDW(true);
    try {
      const r = await fetch(`${API}/api/document/${deleting}`, {
        method: "DELETE",
        headers: { "X-Auth-Token": getToken() },
      });
      if (!r.ok) { const d = await r.json(); throw new Error(d.detail || "Delete failed"); }
      setDeleting(null);
      setDetail(null);
      fetchRecords(page);
    } catch (e) { alert(e.message); }
    finally { setDW(false); }
  }

  const logout = async () => {
    await fetch(`${API}/api/auth/logout`, { method: "POST", headers: { "X-Auth-Token": getToken() } }).catch(() => {});
    localStorage.clear(); router.push("/");
  };

  const kindTag = k => <span className={`tag ${k === "letter" ? "tag-letter" : "tag-order"}`}>{k === "letter" ? "Letter" : "Office Order"}</span>;
  const dirTag  = d => <span className={`tag ${d === "incoming" ? "tag-in" : "tag-out"}`}>{d}</span>;
  const statTag = s => <span className={`tag ${s === "completed" ? "tag-done" : s === "failed" ? "tag-failed" : "tag-pending"}`}>{s}</span>;

  const canDelete = (rec) => user?.role === "admin" || user?.role === "manager";

  if (!user) return <div className="loading-center"><div className="spinner" />Loading…</div>;

  return (
    <div className="shell">
      <Sidebar user={user} active="records" onLogout={logout} />
      <main className="main">
        <div className="page-title">Records</div>
        <div className="page-sub">{total} document{total !== 1 ? "s" : ""} found</div>

        <div className="card">
          {loading ? (
            <div className="loading-center"><div className="spinner" />Loading records…</div>
          ) : records.length === 0 ? (
            <div style={{ color: "var(--muted)", textAlign: "center", padding: "40px", fontSize: 14 }}>
              No records yet. Go to Scan to upload your first document.
            </div>
          ) : (
            <>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Filename</th>
                      <th>Type</th>
                      <th>Direction</th>
                      {user.role === "admin" && <th>Role</th>}
                      <th>Status</th>
                      <th>Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((rec, i) => (
                      <tr key={rec.id}>
                        <td style={{ color: "var(--muted)" }}>{(page - 1) * 20 + i + 1}</td>
                        <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                          title={rec.original_filename || rec.filename}>
                          {rec.original_filename || rec.filename || "—"}
                        </td>
                        <td>{kindTag(rec.document_kind)}</td>
                        <td>{dirTag(rec.direction)}</td>
                        {user.role === "admin" && <td style={{ color: "var(--muted)" }}>{rec.role}</td>}
                        <td>{statTag(rec.status)}</td>
                        <td style={{ color: "var(--muted)", fontSize: 12 }}>
                          {rec.created_at ? new Date(rec.created_at).toLocaleDateString() : "—"}
                        </td>
                        <td>
                          <div style={{ display: "flex", gap: 6 }}>
                            <button
                              onClick={() => openDetail(rec.id)}
                              style={styles.btnView}
                            >
                              View
                            </button>
                            {canDelete(rec) && (
                              <button
                                onClick={() => setDeleting(rec.id)}
                                style={styles.btnDelete}
                              >
                                Delete
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="pagination">
                <button className="page-btn" disabled={page <= 1} onClick={() => fetchRecords(page - 1)}>← Prev</button>
                <span className="page-info">Page {page} of {pages}</span>
                <button className="page-btn" disabled={page >= pages} onClick={() => fetchRecords(page + 1)}>Next →</button>
              </div>
            </>
          )}
        </div>

        {/* ── Detail Modal ── */}
        {detail && (
          <div style={styles.overlay} onClick={() => setDetail(null)}>
            <div style={styles.modal} onClick={e => e.stopPropagation()}>
              {detail.loading ? (
                <div className="loading-center"><div className="spinner" />Loading…</div>
              ) : detail.error ? (
                <div style={{ color: "#ef4444" }}>{detail.error}</div>
              ) : (
                <>
                  <div style={styles.modalHeader}>
                    <div>
                      <div style={styles.modalTitle}>{detail.filename || "Document"}</div>
                      <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                        {kindTag(detail.document_kind)}
                        {dirTag(detail.direction)}
                        {statTag(detail.status)}
                      </div>
                    </div>
                    <button onClick={() => setDetail(null)} style={styles.closeBtn}>✕</button>
                  </div>

                  <div style={styles.modalMeta}>
                    {detail.role && <span>Role: <strong>{detail.role}</strong></span>}
                    {detail.created_at && <span>Uploaded: <strong>{new Date(detail.created_at).toLocaleString()}</strong></span>}
                    {detail.confidence_score && <span>Confidence: <strong>{Math.round(detail.confidence_score * 100)}%</strong></span>}
                  </div>

                  {/* Document image preview */}
                  {detail.file_url && (
                    <>
                      <div style={styles.sectionLabel}>Document Image</div>
                      <div style={styles.imageWrap}>
                        <img
                          src={`${API}${detail.file_url}`}
                          alt="Document"
                          style={styles.docImage}
                          onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }}
                        />
                        <div style={{ ...styles.imageError, display: "none" }}>
                          <span>📄</span>
                          <span style={{ fontSize: 13, color: "var(--muted)" }}>
                            Preview not available for this file type.{" "}
                            <a href={`${API}${detail.file_url}`} target="_blank" rel="noreferrer"
                              style={{ color: "#4f6ef7" }}>Download file</a>
                          </span>
                        </div>
                      </div>
                    </>
                  )}

                  <div style={{ ...styles.sectionLabel, marginTop: 20 }}>Extracted Fields</div>
                  <div style={styles.fieldsGrid}>
                    {Object.entries(FIELD_LABELS).map(([key, label]) => (
                      <div key={key} style={key === "notes" || key === "subject" || key === "to_field" ? { ...styles.fieldItem, gridColumn: "span 2" } : styles.fieldItem}>
                        <div style={styles.fieldLabel}>{label}</div>
                        <div style={styles.fieldValue}>
                          {detail.fields?.[key] || <span style={{ color: "#aab0c4" }}>—</span>}
                        </div>
                      </div>
                    ))}
                  </div>

                  {canDelete(detail) && (
                    <div style={{ marginTop: 24, display: "flex", justifyContent: "flex-end" }}>
                      <button
                        onClick={() => { setDeleting(detail.id); }}
                        style={styles.btnDeleteLg}
                      >
                        🗑 Delete Record
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* ── Delete Confirm Modal ── */}
        {deleting && (
          <div style={styles.overlay}>
            <div style={{ ...styles.modal, maxWidth: 400 }}>
              <div style={styles.modalTitle}>Delete Record?</div>
              <p style={{ fontSize: 14, color: "var(--muted)", margin: "12px 0 24px" }}>
                This will permanently delete the document and its file. This cannot be undone.
              </p>
              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button className="btn-secondary" onClick={() => setDeleting(null)} disabled={deleteWorking}>
                  Cancel
                </button>
                <button style={styles.btnDeleteLg} onClick={confirmDelete} disabled={deleteWorking}>
                  {deleteWorking ? "Deleting…" : "Yes, Delete"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

const styles = {
  btnView: {
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 500,
    background: "#f0f3ff",
    color: "#4f6ef7",
    border: "1px solid #d0d8ff",
    borderRadius: 6,
    cursor: "pointer",
  },
  btnDelete: {
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 500,
    background: "#fff0f0",
    color: "#ef4444",
    border: "1px solid #ffd0d0",
    borderRadius: 6,
    cursor: "pointer",
  },
  btnDeleteLg: {
    padding: "8px 18px",
    fontSize: 13,
    fontWeight: 600,
    background: "#ef4444",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
  },
  overlay: {
    position: "fixed", inset: 0,
    background: "rgba(0,0,0,0.45)",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 1000,
    padding: 20,
  },
  modal: {
    background: "#fff",
    borderRadius: 14,
    padding: "28px 32px",
    width: "100%",
    maxWidth: 620,
    maxHeight: "85vh",
    overflowY: "auto",
    boxShadow: "0 8px 48px rgba(0,0,0,0.18)",
  },
  modalHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: 600,
    color: "#1a2340",
  },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: 18,
    color: "#aab0c4",
    cursor: "pointer",
    padding: "0 4px",
  },
  modalMeta: {
    display: "flex",
    gap: 20,
    fontSize: 13,
    color: "#7a849e",
    marginBottom: 20,
    paddingBottom: 16,
    borderBottom: "1px solid #f0f1f5",
    flexWrap: "wrap",
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "#aab0c4",
    marginBottom: 14,
  },
  fieldsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 14,
  },
  fieldItem: {
    background: "#f8f9ff",
    borderRadius: 8,
    padding: "10px 14px",
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: "#aab0c4",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    marginBottom: 4,
  },
  fieldValue: {
    fontSize: 14,
    color: "#1a2340",
    wordBreak: "break-word",
  },
  imageWrap: {
    border: "1px solid #e4e7f0",
    borderRadius: 10,
    overflow: "hidden",
    marginBottom: 20,
    background: "#f8f9ff",
    maxHeight: 480,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  docImage: {
    width: "100%",
    maxHeight: 480,
    objectFit: "contain",
    display: "block",
  },
  imageError: {
    padding: "32px 20px",
    flexDirection: "column",
    alignItems: "center",
    gap: 10,
    fontSize: 32,
    width: "100%",
  },
};