import { useState } from 'react'
import { api } from '../api.js'
import ChartCard from '../components/ChartCard.jsx'

export default function AutoVizPage({ dataset }) {
  const [plan, setPlan] = useState(null)
  const [charts, setCharts] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const generate = async () => {
    setBusy(true)
    setError(null)
    setCharts(null)
    try {
      const planResp = await api.autoPlan(dataset.dataset_id)
      setPlan(planResp)
      const execResp = await api.autoExecute(dataset.dataset_id, planResp.plan)
      setCharts(execResp.charts)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const rejected = plan?.rejected || []

  return (
    <div className="page">
      <div className="toolbar">
        <button className="btn btn-primary" onClick={generate} disabled={busy || !dataset}>
          {busy ? 'Working… (LLM planning → validation → rendering)' : 'Auto-generate charts'}
        </button>
        {plan && !busy && (
          <span className="source-note">
            Plan source: <strong>{plan.source === 'llm' ? 'local LLM' : 'statistical fallback (degraded mode)'}</strong>
          </span>
        )}
      </div>

      {error && <div className="alert-error">{error}</div>}

      {plan && (
        <div className="plan-summary">
          {plan.plan.length} charts planned · {rejected.length} rejected by domain rules
          {rejected.length > 0 && (
            <ul className="rejected-list">
              {rejected.map((r, i) => (
                <li key={i}><code>{r.spec.chart_type}</code> ({r.spec.title}): {r.reason}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="chart-grid">
        {(charts || []).map((c, i) => (
          <ChartCard
            key={i}
            title={c.spec.title}
            rationale={c.rationale}
            option={c.ok ? c.option : null}
            error={c.ok ? null : c.error}
            functionsUsed={c.functions_used}
          />
        ))}
      </div>

      {!charts && !busy && !error && (
        <p className="hint">Click "Auto-generate charts" — the local LLM proposes a plan from dataset metadata, domain rules filter it, and charts render locally.</p>
      )}
    </div>
  )
}
