import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, BarChart3, Check, Database, FileText, FileUp, Lock, Trash2, X } from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE || "/api";
const SOURCES = [
  { id: "sap", label: "SAP", detail: "Fuel and procurement", sample: "sap_material_documents.csv" },
  { id: "utility", label: "Utility", detail: "Electricity meters", sample: "utility_meter_export.csv" },
  { id: "travel", label: "Travel", detail: "Flights, hotel, ground", sample: "concur_travel_expenses.csv" },
];

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

  async function clearData() {
    setBusy(true);
    const res = await fetch(`${API}/clear/`, { method: "POST" });
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
    setUpload({ ...upload, file: null });
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
  const maxSource = Math.max(...(data.stats.source_totals || []).map((item) => Number(item.co2e || 0)), 1);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Breathe ESG prototype</p>
          <h1>Enterprise emissions review</h1>
          <p className="subtitle">Normalize SAP, utility, and travel data before audit sign-off.</p>
        </div>
        <div className="actions">
          <button onClick={lockApproved} disabled={busy}><Lock size={16} /> Lock approved</button>
          <button className="ghost danger" onClick={clearData} disabled={busy}><Trash2 size={16} /> Clear</button>
        </div>
      </header>

      <section className="metrics">
        <div><span>Total rows</span><strong>{data.stats.rows || 0}</strong><em>Imported activities</em></div>
        <div><span>CO2e kg</span><strong>{formatKg(data.stats.co2e_kg)}</strong><em>Normalized total</em></div>
        <div><span>Needs review</span><strong>{needsReview}</strong><em>Pending or flagged</em></div>
        <div><span>Locked</span><strong>{data.stats.status_counts.locked || 0}</strong><em>Audit-ready rows</em></div>
      </section>

      <section className="source-strip">
        {SOURCES.map((sourceItem) => {
          const total = (data.stats.source_totals || []).find((item) => item.batch__source_type === sourceItem.id);
          const co2e = Number(total?.co2e || 0);
          return (
            <div className="source-card" key={sourceItem.id}>
              <div>
                <FileText size={18} />
                <span>{sourceItem.label}</span>
              </div>
              <strong>{formatKg(co2e)} kg</strong>
              <small>{sourceItem.detail}</small>
              <div className="bar"><i style={{ width: `${Math.max(4, (co2e / maxSource) * 100)}%` }} /></div>
            </div>
          );
        })}
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

          <div className="sample-links">
            <h2>Sample CSVs</h2>
            {SOURCES.map((item) => (
              <a key={item.id} href={`${API}/samples/${item.sample}`}>{item.label} sample</a>
            ))}
          </div>

          <h2>Batches</h2>
          <div className="batches">
            {data.batches.length === 0 && <div className="empty-small">No uploads yet</div>}
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
            <div className="review-title"><BarChart3 size={18} /> Review queue</div>
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
            {filtered.length === 0 && (
              <div className="empty-state">
                <strong>No activity rows yet</strong>
                <span>Upload SAP, utility, or travel CSV data to populate the analyst queue.</span>
              </div>
            )}
            {filtered.map((row) => (
              <div className="row" key={row.id}>
                <span><strong>{row.batch.source_type}</strong><small>{row.external_id}</small></span>
                <span><strong>{row.description}</strong><small>{row.facility?.name || "Unmapped facility"} - {row.scope.replace("_", " ")}</small></span>
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
