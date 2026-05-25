import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, Check, Database, FileUp, Lock, RefreshCw, X } from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE || "/api";

function formatKg(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function App() {
  const [data, setData] = useState({ stats: { status_counts: {}, source_totals: [] }, batches: [], activities: [] });
  const [status, setStatus] = useState("all");
  const [source, setSource] = useState("all");
  const [busy, setBusy] = useState(false);
  const [upload, setUpload] = useState({ source_type: "sap", file: null });

  async function load() {
    const res = await fetch(`${API}/dashboard/`);
    setData(await res.json());
  }

  async function seed() {
    setBusy(true);
    const res = await fetch(`${API}/seed/`, { method: "POST" });
    setData(await res.json());
    setBusy(false);
  }

  async function review(id, nextStatus, note = "") {
    setBusy(true);
    await fetch(`${API}/activities/${id}/review/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: nextStatus, actor: "Demo analyst", note }),
    });
    await load();
    setBusy(false);
  }

  async function lockApproved() {
    setBusy(true);
    await fetch(`${API}/lock-approved/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor: "Lead analyst" }),
    });
    await load();
    setBusy(false);
  }

  async function submitUpload(event) {
    event.preventDefault();
    if (!upload.file) return;
    const form = new FormData();
    form.append("source_type", upload.source_type);
    form.append("file", upload.file);
    setBusy(true);
    await fetch(`${API}/upload/`, { method: "POST", body: form });
    await load();
    setBusy(false);
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => data.activities.filter((row) => {
    const statusMatch = status === "all" || row.status === status;
    const sourceMatch = source === "all" || row.batch.source_type === source;
    return statusMatch && sourceMatch;
  }), [data.activities, status, source]);

  const needsReview = (data.stats.status_counts.pending || 0) + (data.stats.status_counts.flagged || 0);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Breathe ESG prototype</p>
          <h1>Analyst ingestion review</h1>
        </div>
        <div className="actions">
          <button onClick={seed} disabled={busy}><RefreshCw size={16} /> Seed realistic data</button>
          <button onClick={lockApproved} disabled={busy}><Lock size={16} /> Lock approved</button>
        </div>
      </header>

      <section className="metrics">
        <div><span>Total rows</span><strong>{data.stats.rows || 0}</strong></div>
        <div><span>CO2e kg</span><strong>{formatKg(data.stats.co2e_kg)}</strong></div>
        <div><span>Needs review</span><strong>{needsReview}</strong></div>
        <div><span>Locked</span><strong>{data.stats.status_counts.locked || 0}</strong></div>
      </section>

      <section className="workbench">
        <aside className="panel">
          <h2>Ingestion</h2>
          <form onSubmit={submitUpload} className="upload">
            <label>
              Source type
              <select value={upload.source_type} onChange={(e) => setUpload({ ...upload, source_type: e.target.value })}>
                <option value="sap">SAP fuel/procurement</option>
                <option value="utility">Utility electricity</option>
                <option value="travel">Corporate travel</option>
              </select>
            </label>
            <label>
              CSV file
              <input type="file" accept=".csv" onChange={(e) => setUpload({ ...upload, file: e.target.files[0] })} />
            </label>
            <button disabled={busy || !upload.file}><FileUp size={16} /> Upload</button>
          </form>

          <h2>Batches</h2>
          <div className="batches">
            {data.batches.map((batch) => (
              <div className="batch" key={batch.id}>
                <Database size={16} />
                <div>
                  <strong>{batch.source_type}</strong>
                  <span>{batch.row_count} rows, {batch.failed_count} failed</span>
                  <small>{batch.ingestion_mode}</small>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <section className="review">
          <div className="filters">
            <select value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="all">All sources</option>
              <option value="sap">SAP</option>
              <option value="utility">Utility</option>
              <option value="travel">Travel</option>
            </select>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All statuses</option>
              <option value="flagged">Flagged</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="locked">Locked</option>
            </select>
          </div>

          <div className="table">
            <div className="row header">
              <span>Source</span><span>Activity</span><span>Quantity</span><span>CO2e</span><span>Status</span><span>Actions</span>
            </div>
            {filtered.map((row) => (
              <div className="row" key={row.id}>
                <span><strong>{row.batch.source_type}</strong><small>{row.external_id}</small></span>
                <span><strong>{row.description}</strong><small>{row.facility?.name || "Unmapped facility"} · {row.scope.replace("_", " ")}</small></span>
                <span>{Number(row.normalized_quantity).toLocaleString()} {row.normalized_unit}<small>{row.activity_date}</small></span>
                <span>{formatKg(row.co2e_kg)} kg</span>
                <span className={`pill ${row.status}`}>{row.status}</span>
                <span className="row-actions">
                  {row.suspicion_reason && <button title={row.suspicion_reason} className="icon warn"><AlertTriangle size={16} /></button>}
                  <button title="Approve" onClick={() => review(row.id, "approved")} disabled={busy || row.status === "locked"}><Check size={16} /></button>
                  <button title="Reject" onClick={() => review(row.id, "rejected", "Rejected in dashboard")} disabled={busy || row.status === "locked"}><X size={16} /></button>
                </span>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
