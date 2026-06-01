"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();

  const [form, setForm] = useState({
    org_name: "",
    slug: "",
    display_name: "",
    username: "",
    password: "",
    confirm_password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [slugManual, setSlugManual] = useState(false);

  // Auto-generate slug from org name
  function handleOrgNameChange(e) {
    const val = e.target.value;
    setForm((f) => ({
      ...f,
      org_name: val,
      slug: slugManual
        ? f.slug
        : val
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, ""),
    }));
  }

  function handleSlugChange(e) {
    setSlugManual(true);
    setForm((f) => ({
      ...f,
      slug: e.target.value
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, "")
        .replace(/^-+/, ""),
    }));
  }

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirm_password) {
      setError("Passwords do not match.");
      return;
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (!form.slug) {
      setError("Office ID (slug) is required.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
                org_name: form.org_name,
                slug: form.slug,
                admin_username: form.username,
                admin_password: form.password,
                admin_display_name: form.display_name || form.username,
            }),
    });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Registration failed. Please try again.");
        return;
      }

      // Store auth — same keys as login page
      localStorage.setItem("dswops_token", data.token);
      localStorage.setItem(
        "dswops_user",
        JSON.stringify({
          username: form.username,
          role: "admin",
          org_id: data.org_id,
          org_name: form.org_name,
          plan: "free",
        })
      );

      router.push("/dashboard");
    } catch (err) {
      setError("Cannot connect to server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.root}>
      {/* Left panel */}
      <div style={styles.left}>
        <div style={styles.leftInner}>
          <div style={styles.brand}>
            <div style={styles.brandIcon}>
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <rect width="28" height="28" rx="8" fill="#4f6ef7" />
                <path
                  d="M7 8h14M7 12h10M7 16h12M7 20h8"
                  stroke="#fff"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <span style={styles.brandName}>DocFlow</span>
          </div>

          <h1 style={styles.leftTitle}>
            Your office.
            <br />
            Your workspace.
          </h1>
          <p style={styles.leftSub}>
            Register your office in under a minute. Scan, extract, and manage
            documents — all in one place.
          </p>

          <div style={styles.featureList}>
            {[
              "Multi-user office workspace",
              "OCR-powered document scanning",
              "Role-based access control",
              "Full audit trail",
            ].map((f) => (
              <div key={f} style={styles.featureItem}>
                <div style={styles.featureDot} />
                <span>{f}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div style={styles.right}>
        <div style={styles.formCard}>
          <div style={styles.formHeader}>
            <h2 style={styles.formTitle}>Register your office</h2>
            <p style={styles.formSub}>
              Already registered?{" "}
              <a href="/" style={styles.link}>
                Sign in
              </a>
            </p>
          </div>

          <form onSubmit={handleSubmit} style={styles.form}>
            {/* Section: Office */}
            <div style={styles.sectionLabel}>Office Details</div>

            <div style={styles.field}>
              <label style={styles.label}>Office / Organization Name</label>
              <input
                style={styles.input}
                type="text"
                name="org_name"
                placeholder="e.g. Directorate of Wildlife KPK"
                value={form.org_name}
                onChange={handleOrgNameChange}
                required
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>
                Office ID{" "}
                <span style={styles.labelHint}>
                  (used in your workspace URL)
                </span>
              </label>
              <div style={styles.slugRow}>
                <span style={styles.slugPrefix}>docflow.app/</span>
                <input
                  style={{ ...styles.input, ...styles.slugInput }}
                  type="text"
                  name="slug"
                  placeholder="wildlife-kpk"
                  value={form.slug}
                  onChange={handleSlugChange}
                  required
                />
              </div>
            </div>

            {/* Section: Admin account */}
            <div style={{ ...styles.sectionLabel, marginTop: 24 }}>
              Admin Account
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Your Name</label>
              <input
                style={styles.input}
                type="text"
                name="display_name"
                placeholder="e.g. Muhammad Muizz"
                value={form.display_name}
                onChange={handleChange}
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Username</label>
              <input
                style={styles.input}
                type="text"
                name="username"
                placeholder="admin"
                value={form.username}
                onChange={handleChange}
                required
                autoComplete="username"
              />
            </div>

            <div style={styles.twoCol}>
              <div style={styles.field}>
                <label style={styles.label}>Password</label>
                <input
                  style={styles.input}
                  type="password"
                  name="password"
                  placeholder="Min. 6 characters"
                  value={form.password}
                  onChange={handleChange}
                  required
                  autoComplete="new-password"
                />
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Confirm Password</label>
                <input
                  style={styles.input}
                  type="password"
                  name="confirm_password"
                  placeholder="Repeat password"
                  value={form.confirm_password}
                  onChange={handleChange}
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>

            {error && <div style={styles.error}>{error}</div>}

            <button
              type="submit"
              style={loading ? { ...styles.btn, ...styles.btnDisabled } : styles.btn}
              disabled={loading}
            >
              {loading ? (
                <span style={styles.btnInner}>
                  <span style={styles.spinner} /> Creating workspace…
                </span>
              ) : (
                "Create Office Workspace"
              )}
            </button>
          </form>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        input:focus {
          outline: none;
          border-color: #4f6ef7 !important;
          box-shadow: 0 0 0 3px rgba(79,110,247,0.12);
        }

        input::placeholder { color: #aab0c4; }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

const styles = {
  root: {
    display: "flex",
    minHeight: "100vh",
    fontFamily: "'DM Sans', sans-serif",
    background: "#f5f6fa",
  },

  // ── Left panel ──────────────────────────────
  left: {
    width: "42%",
    background: "linear-gradient(145deg, #1a2340 0%, #2d3a6b 60%, #3d52a0 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "60px 48px",
    position: "relative",
    overflow: "hidden",
  },
  leftInner: {
    position: "relative",
    zIndex: 1,
    animation: "fadeUp .5s ease both",
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 48,
  },
  brandIcon: { lineHeight: 0 },
  brandName: {
    fontSize: 22,
    fontWeight: 600,
    color: "#fff",
    letterSpacing: "-0.3px",
  },
  leftTitle: {
    fontFamily: "'DM Serif Display', serif",
    fontSize: 40,
    lineHeight: 1.15,
    color: "#fff",
    marginBottom: 16,
  },
  leftSub: {
    fontSize: 15,
    color: "rgba(255,255,255,0.65)",
    lineHeight: 1.6,
    marginBottom: 40,
    maxWidth: 320,
  },
  featureList: {
    display: "flex",
    flexDirection: "column",
    gap: 14,
  },
  featureItem: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    color: "rgba(255,255,255,0.85)",
    fontSize: 14,
  },
  featureDot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: "#4f6ef7",
    flexShrink: 0,
    boxShadow: "0 0 0 3px rgba(79,110,247,0.3)",
  },

  // ── Right panel ─────────────────────────────
  right: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 24px",
    overflowY: "auto",
  },
  formCard: {
    background: "#fff",
    borderRadius: 16,
    padding: "40px 44px",
    width: "100%",
    maxWidth: 560,
    boxShadow: "0 4px 32px rgba(0,0,0,0.07)",
    animation: "fadeUp .45s ease both",
  },
  formHeader: { marginBottom: 28 },
  formTitle: {
    fontSize: 24,
    fontWeight: 600,
    color: "#1a2340",
    marginBottom: 6,
    letterSpacing: "-0.3px",
  },
  formSub: { fontSize: 14, color: "#7a849e" },
  link: { color: "#4f6ef7", textDecoration: "none", fontWeight: 500 },

  form: { display: "flex", flexDirection: "column", gap: 16 },

  sectionLabel: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "#aab0c4",
    paddingBottom: 4,
    borderBottom: "1px solid #f0f1f5",
  },

  field: { display: "flex", flexDirection: "column", gap: 6 },
  label: { fontSize: 13, fontWeight: 500, color: "#3d4666" },
  labelHint: { fontWeight: 400, color: "#aab0c4" },

  input: {
    padding: "10px 14px",
    border: "1.5px solid #e4e7f0",
    borderRadius: 8,
    fontSize: 14,
    color: "#1a2340",
    background: "#fafbff",
    transition: "border-color .15s, box-shadow .15s",
    width: "100%",
  },

  slugRow: {
    display: "flex",
    alignItems: "center",
    border: "1.5px solid #e4e7f0",
    borderRadius: 8,
    background: "#fafbff",
    overflow: "hidden",
    transition: "border-color .15s, box-shadow .15s",
  },
  slugPrefix: {
    padding: "10px 12px",
    fontSize: 13,
    color: "#aab0c4",
    background: "#f0f1f8",
    borderRight: "1.5px solid #e4e7f0",
    whiteSpace: "nowrap",
    userSelect: "none",
  },
  slugInput: {
    border: "none",
    borderRadius: 0,
    background: "transparent",
    flex: 1,
  },

  twoCol: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 14,
  },

  error: {
    background: "#fff0f0",
    border: "1px solid #ffd0d0",
    color: "#c0392b",
    borderRadius: 8,
    padding: "10px 14px",
    fontSize: 13,
  },

  btn: {
    marginTop: 4,
    padding: "13px",
    background: "#4f6ef7",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    transition: "background .15s, transform .1s",
    letterSpacing: "-0.1px",
  },
  btnDisabled: {
    background: "#8fa5f9",
    cursor: "not-allowed",
  },
  btnInner: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  spinner: {
    display: "inline-block",
    width: 14,
    height: 14,
    border: "2px solid rgba(255,255,255,0.3)",
    borderTopColor: "#fff",
    borderRadius: "50%",
    animation: "spin .7s linear infinite",
  },
};