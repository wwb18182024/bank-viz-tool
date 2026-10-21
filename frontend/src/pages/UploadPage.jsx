import { useState } from 'react'
import { api } from '../api.js'

export default function UploadPage({ dataset, onUploaded, health }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const doUpload = async (file) => {
    if (!file) return
    setBusy(true)
    setError(null)
    try {
      const info = await api.upload(file)
      const meta = await api.metadata(info.dataset_id)
      onUploaded({ ...info, meta })
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const meta = dataset?.meta
  const columns = meta?.columns || []

  return (
    <div className="page">
      <div className="upload-zone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); doUpload(e.dataTransfer.files[0]) }}>
        <input
          id="file-input" type="file" accept=".csv,.xlsx,.xls" style={{ display: 'none' }}
          onChange={(e) => doUpload(e.target.files[0])}
        />
        {busy ? (
          <p>Loading & profiling dataset…</p>
        ) : (
          <>
            <p className="upload-main">Drop a CSV / Excel file here, or</p>
            <button className="btn btn-primary" onClick={() => document.getElementById('file-input').click()}>
              Choose file
            </button>
            <p className="upload-note">All processing happens on this machine. Nothing is uploaded to the internet.</p>
          </>
        )}
        {error && <div className="alert-error">{error}</div>}
      </div>

      {meta && (
        <div className="overview">
          <div className="stats-row">
            <div className="stat-card"><span className="stat-num">{meta.n_rows.toLocaleString()}</span><span>rows</span></div>
            <div className="stat-card"><span className="stat-num">{meta.n_columns}</span><span>columns</span></div>
            <div className="stat-card"><span className="stat-num">{columns.filter(c => c.missing > 0).length}</span><span>cols with missing</span></div>
            <div className="stat-card"><span className="stat-num">{dataset.filename}</span><span className="small">{dataset.filename}</span></div>
          </div>
          <table className="meta-table">
            <thead>
              <tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th><th>Range / Top values</th></tr>
            </thead>
            <tbody>
              {columns.map((c) => (
                <tr key={c.name}>
                  <td className="mono">{c.name}</td>
                  <td><span className={`badge badge-${c.semantic_type}`}>{c.semantic_type}</span></td>
                  <td>{c.missing > 0 ? `${c.missing} (${c.missing_pct}%)` : '—'}</td>
                  <td>{c.unique}</td>
                  <td className="small">
                    {c.min !== undefined && c.min !== null
                      ? `${c.min} – ${c.max}`
                      : (c.top_values || []).slice(0, 3).map(v => `${v.value} (${v.count})`).join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {health && !health.ollama.reachable && (
        <div className="alert-warn">
          Local LLM (Ollama) is not running — auto mode will use the statistical fallback recommender.
          Run <code>ollama serve</code> and <code>ollama pull {health.ollama.model}</code> for full LLM functionality.
        </div>
      )}
    </div>
  )
}
