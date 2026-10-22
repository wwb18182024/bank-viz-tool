import { useEffect, useState } from 'react'
import { api } from '../api.js'
import ChartCard from '../components/ChartCard.jsx'

export default function AutoVizPage({ dataset }) {
  const [plan, setPlan] = useState(null)
  const [charts, setCharts] = useState(null)
  const [stage, setStage] = useState(null) // null | 'planning' | 'rendering'
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState(null)

  // Elapsed-seconds ticker while a stage is running, so the wait is visibly
  // progressing rather than looking frozen (LLM calls take 30s+ on CPU).
  useEffect(() => {
    if (!stage) return undefined
    setElapsed(0)
    const t0 = Date.now()
    const id = setInterval(() => setElapsed(Math.round((Date.now() - t0) / 1000)), 1000)
    return () => clearInterval(id)
  }, [stage])

  const generate = async () => {
    setStage('planning')
    setError(null)
    setCharts(null)
    setPlan(null)
    try {
      const planResp = await api.autoPlan(dataset.dataset_id)
      setPlan(planResp)
      setStage('rendering')
      const execResp = await api.autoExecute(dataset.dataset_id, planResp.plan)
      setCharts(execResp.charts)
    } catch (e) {
      setError(e.message)
    } finally {
      setStage(null)
    }
  }

  const busy = stage !== null
  const rejected = plan?.rejected || []

  return (
    <div className="page">
      <div className="toolbar">
        <button className="btn btn-primary" onClick={generate} disabled={busy || !dataset}>
          {busy ? 'Working…' : 'Auto-generate charts'}
        </button>
        {plan && !busy && (
          <span className="source-note">
            Plan source: <strong>{plan.source === 'llm' ? 'local LLM' : 'statistical fallback (degraded mode)'}</strong>
          </span>
        )}
      </div>

      {stage && (
        <div className="progress-panel" role="status">
          <div className="spinner" aria-hidden="true" />
          <div>
            <strong>
              {stage === 'planning'
                ? 'Local LLM is generating a visualisation plan…'
                : 'Validating & rendering charts…'}
            </strong>
            <div className="progress-hint">
              {stage === 'planning'
                ? `${elapsed}s elapsed · this runs entirely on your machine — the first call includes model loading and can take 1–2 minutes. Nothing is frozen; later runs are much faster.`
                : `${elapsed}s elapsed`}
            </div>
          </div>
        </div>
      )}

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
