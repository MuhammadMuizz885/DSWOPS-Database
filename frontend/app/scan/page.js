"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "../dashboard/page";

const API = "http://localhost:8000";
const getToken = () => localStorage.getItem("dswops_token") || "";
const getUser  = () => { try { return JSON.parse(localStorage.getItem("dswops_user")); } catch { return null; } };

const ROLE_LABELS = {
  admin:   "Admin",
  manager: "Manager",
  officer: "Officer",
  viewer:  "Viewer",
};

const EMPTY_FIELDS = {
  doc_number: "",
  date:       "",
  subject:    "",
  from_field: "",
  to_field:   "",
  ccwl_no:    "",
  notes:      "",
};

const FIELD_META = [
  { key: "doc_number", label: "Document / Ref No.",   placeholder: "e.g. No. 1234/KPK/2026",   half: true },
  { key: "date",       label: "Date",                  placeholder: "e.g. 2026-05-31",           half: true },
  { key: "subject",    label: "Subject",               placeholder: "Subject line or title",      half: false },
  { key: "from_field", label: "From",                  placeholder: "Issuing party / sender",     half: true },
  { key: "to_field",   label: "To",                    placeholder: "Recipient / addressee",      half: true },
  { key: "ccwl_no",    label: "CCWL",                  placeholder: "Copy forwarded to…",         half: false },
  { key: "notes",      label: "Notes",                 placeholder: "Any additional notes…",      half: false, multiline: true },
];

export default function ScanPage() {
  const router = useRouter();
  const [user, setUser]     = useState(null);
  const [step, setStep]     = useState(1);

  // Step 1
  const [role, setRole]     = useState("");
  const [kind, setKind]     = useState("letter");
  const [direction, setDir] = useState("incoming");

  // Step 2
  const [file, setFile]         = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [over, setOver]         = useState(false);
  const fileRef = useRef();

  // Step 3
  const [extracting, setExtracting] = useState(false);
  const [fields, setFields]         = useState({ ...EMPTY_FIELDS });
  const [confidence, setConf]       = useState(0);
  const [saving, setSaving]         = useState(false);
  const [saved, setSaved]           = useState(false);

  useEffect(() => {
    const u = getUser();
    if (!u) { router.push("/"); return; }
    setUser(u);
    setRole(u.role === "admin" ? "" : u.role);
  }, []);

  const logout = async () => {
    await fetch(`${API}/api/auth/logout`, { method: "POST", headers: { "X-Auth-Token": getToken() } }).catch(() => {});
    localStorage.clear();
    router.push("/");
  };

  const setField = (key, val) => setFields(f => ({ ...f, [key]: val }));

  async function handleUpload(f) {
    setFile(f);
    setUploading(true);
    const fd = new FormData();
    fd.append("file", f);
    try {
      console.log("Token:", getToken());
      console.log("User:", getUser());
      const r = await fetch(`${API}/api/upload`, {
        method: "POST",
        headers: {
          "X-Auth-Token":     getToken(),
          "X-Document-Kind":  kind,
          "X-Direction":      direction,
          "X-Role":           role,
        },
        body: fd,
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Upload failed");
      setUploadId(d.upload_id);
      setStep(2);
    } catch (e) { alert(e.message); }
    finally { setUploading(false); }
  }

  async function runOCR() {
    setExtracting(true);
    try {
      const r = await fetch(`${API}/api/extract/${uploadId}`, {
        method: "POST",
        headers: { "X-Auth-Token": getToken() },
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Extraction failed");
      setFields({ ...EMPTY_FIELDS, ...(d.extracted_fields || {}) });
      setConf(d.confidence_score || 0);
      setStep(3);
    } catch (e) { alert(e.message); }
    finally { setExtracting(false); }
  }

  async function handleSave() {
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/save/${uploadId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Auth-Token": getToken() },
        body: JSON.stringify(fields),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Save failed");
      setSaved(true);
      setTimeout(() => {
        setStep(1); setFile(null); setUploadId(null);
        setFields({ ...EMPTY_FIELDS }); setConf(0); setSaved(false);
      }, 2000);
    } catch (e) { alert(e.message); }
    finally { setSaving(false); }
  }

  function reset() {
    setStep(1); setFile(null); setUploadId(null);
    setFields({ ...EMPTY_FIELDS }); setConf(0); setSaved(false);
  }

  if (!user) return <div className="loading-center"><div className="spinner" />Loading…</div>;

  const confColor = confidence >= 70 ? "#22c55e" : confidence >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="shell">
      <Sidebar user={user} active="scan" onLogout={logout} />
      <main className="main">
        <div className="page-title">Scan Document</div>
        <div className="page-sub">Upload a document, run OCR, review and save extracted fields.</div>

        {/* Step pills */}
        <div className="step-pills">
          {["Document Details", "Upload File", "Review & Save"].map((s, i) => (
            <div key={i} className={`step-pill${step === i + 1 ? " active" : step > i + 1 ? " done" : ""}`}>
              {step > i + 1 ? "✓ " : ""}{i + 1}. {s}
            </div>
          ))}
        </div>

        {/* ── STEP 1 — Details ── */}
        {step === 1 && (
          <div className="card">
            <div className="section-label">Document Type</div>
            <div className="kind-tabs">
              {["letter", "office_order"].map(k => (
                <button key={k} className={`kind-tab${kind === k ? " selected" : ""}`} onClick={() => setKind(k)}>
                  {k === "letter" ? "📄 Letter" : "📋 Office Order"}
                </button>
              ))}
            </div>

            <div className="section-label">Direction</div>
            <div className="dir-tabs">
              {["incoming", "outgoing"].map(d => (
                <button key={d} className={`dir-tab${direction === d ? " selected" : ""}`} onClick={() => setDir(d)}>
                  {d === "incoming" ? "⬇ Incoming" : "⬆ Outgoing"}
                </button>
              ))}
            </div>

            {user.role === "admin" && (
              <>
                <div className="section-label">Processing Role</div>
                <div className="role-grid">
                  {["manager", "officer"].map(r => (
                    <button key={r} className={`role-chip${role === r ? " selected" : ""}`} onClick={() => setRole(r)}>
                      {ROLE_LABELS[r]}
                    </button>
                  ))}
                </div>
              </>
            )}

            {user.role !== "admin" && (
              <div style={{ marginBottom: 20 }}>
                <div className="section-label">Your Role</div>
                <span className="role-chip selected">{ROLE_LABELS[user.role] || user.role}</span>
              </div>
            )}

            <button
              className="btn-primary"
              style={{ width: "auto", padding: "10px 28px" }}
              disabled={!role}
              onClick={() => setStep(1.5)}
            >
              Continue →
            </button>
          </div>
        )}

        {/* ── STEP 1.5 — Upload zone ── */}
        {step === 1.5 && (
          <div className="card">
            <div style={{ marginBottom: 20, display: "flex", alignItems: "center", gap: 12 }}>
              <button className="btn-secondary" onClick={() => setStep(1)}>← Back</button>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>
                {ROLE_LABELS[role]} · {kind === "letter" ? "Letter" : "Office Order"} · {direction}
              </span>
            </div>
            <div className="section-label">Upload Document</div>
            <div
              className={`drop-zone${over ? " over" : ""}`}
              onDragOver={e => { e.preventDefault(); setOver(true); }}
              onDragLeave={() => setOver(false)}
              onDrop={e => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files[0]; if (f) handleUpload(f); }}
              onClick={() => fileRef.current.click()}
            >
              <div className="drop-icon">📁</div>
              <div className="drop-text">
                {uploading
                  ? <><div className="spinner" /> Uploading…</>
                  : <>Drop file here or <span>browse</span><br /><small>PNG, JPG, PDF, DOCX supported</small></>}
              </div>
              <input ref={fileRef} type="file" accept=".png,.jpg,.jpeg,.pdf,.docx" style={{ display: "none" }}
                onChange={e => { const f = e.target.files[0]; if (f) handleUpload(f); }} />
            </div>
          </div>
        )}

        {/* ── STEP 2 — Run OCR ── */}
        {step === 2 && (
          <div className="card">
            <div className="banner-success">✓ Uploaded: {file?.name}</div>
            <div className="section-label">Run OCR & Extract Fields</div>
            <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 20 }}>
              Click below to process the document with Tesseract OCR and auto-fill the fields.
              You can edit anything on the next step.
            </p>
            <button className="btn-primary" style={{ width: "auto", padding: "10px 28px" }}
              onClick={runOCR} disabled={extracting}>
              {extracting ? <><div className="spinner" /> Extracting…</> : "⚡ Run OCR & Extract"}
            </button>
          </div>
        )}

        {/* ── STEP 3 — Review & Save ── */}
        {step === 3 && (
          <div className="card">
            {saved && <div className="banner-success">✓ Document saved successfully!</div>}

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div className="section-label" style={{ marginBottom: 0 }}>Review & Edit Fields</div>
              {confidence > 0 && (
                <span style={{ fontSize: 12, color: confColor, fontWeight: 600 }}>
                  OCR confidence: {confidence}%
                </span>
              )}
            </div>

            <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 20 }}>
              All fields are optional. Edit or fill in anything OCR missed, then save.
            </p>

            <div className="fields-grid">
              {FIELD_META.map(({ key, label, placeholder, half, multiline }) => (
                <div key={key} className={`field-block${half ? " half" : ""}`}>
                  <label className="field-label">{label}</label>
                  {multiline
                    ? <textarea
                        className="field-input"
                        rows={3}
                        placeholder={placeholder}
                        value={fields[key] || ""}
                        onChange={e => setField(key, e.target.value)}
                        style={{ resize: "vertical" }}
                      />
                    : <input
                        className="field-input"
                        placeholder={placeholder}
                        value={fields[key] || ""}
                        onChange={e => setField(key, e.target.value)}
                      />
                  }
                </div>
              ))}
            </div>

            <div className="action-row" style={{ marginTop: 24 }}>
              <button className="btn-success" onClick={handleSave} disabled={saving || saved}>
                {saving ? "Saving…" : "💾 Save Document"}
              </button>
              <button className="btn-secondary" onClick={reset}>
                Start Over
              </button>
            </div>
          </div>
        )}

        <style>{`
          .fields-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }
          .field-block { display: flex; flex-direction: column; gap: 6px; }
          .field-block.half { grid-column: span 1; }
          .field-block:not(.half) { grid-column: span 2; }
          @media (max-width: 600px) {
            .fields-grid { grid-template-columns: 1fr; }
            .field-block.half, .field-block:not(.half) { grid-column: span 1; }
          }
        `}</style>
      </main>
    </div>
  );
}