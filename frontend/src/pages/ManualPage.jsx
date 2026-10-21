import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import ChartCard from '../components/ChartCard.jsx'

const CHARTS_NEEDING_Y = ['bar', 'grouped_bar', 'stacked_bar', 'box', 'scatter', 'line']
const CHARTS_NEEDING_X = ['bar', 'grouped_bar', 'stacked_bar', 'pie', 'histogram', 'box', 'scatter', 'line']

export default function ManualPage({ dataset }) {
  const [options, setOptions] = useState(null)
  const [spec, setSpec] = useState({ chart_type: 'bar', x: '', y: '', group: '', agg: 'mean', bins: 20, filter: '', title: '' })
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (dataset) {
      setOptions(null)
      setResult(null)
      api.manualOptions(dataset.dataset_id).then((opts) => {
        setOptions(opts)
        const cols = opts.columns || []
        const firstCat = cols.find((c) => c.semantic_type === 'categorical')
        const firstNum = cols.find((c) => c.semantic_type === 'numeric')
        setSpec((s) => ({ ...s, x: firstCat?.name || '', y: firstNum?.name || '', title: '' }))
      }).catch((e) => setError(e.message))
    }
  }, [dataset])

  const columns = options?.columns || []
  const numericCols = useMemo(() => columns.filter((c) => c.semantic_type === 'numeric').map((c) => c.name), [columns])
  const anyCols = useMemo(() => columns.filter((c) => c.semantic_type !== 'identifier').map((c) => c.name), [columns])

  if (!dataset) return <div className="page"><p className="hint">Upload a dataset first.</p></div>
  if (!options) return <div className="page"><p className="hint">{error || 'Loading options…'}</p></div>

  const set = (k) => (e) => setSpec((s) => ({ ...s, [k]: e.target.value }))

  const generate = async () => {
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const payload = {
        chart_type: spec.chart_type,
        title: spec.title || `${spec.chart_type} of ${spec.y || spec.x}`,
        rationale: 'Manual chart',
        x: spec.x || null,
        y: CHARTS_NEEDING_Y.includes(spec.chart_type) ? (spec.y || null) : null,
        group: spec.group || null,
        agg: spec.y ? spec.agg : 'count',
        bins: spec.chart_type === 'histogram' ? Number(spec.bins) || 20 : null,
        filter: spec.filter || null,
      }
      const resp = await api.manualChart(dataset.dataset_id, payload)
      setResult(resp)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <div className="manual-form">
        <label>Chart type
          <select value={spec.chart_type} onChange={set('chart_type')}>
            {options.chart_types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </label>
        <label>X axis {spec.chart_type !== 'heatmap' && <span className="req">*</span>}
          <select value={spec.x} onChange={set('x')}>
            <option value="">—</option>
            {anyCols.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        {CHARTS_NEEDING_Y.includes(spec.chart_type) && (
          <label>Y axis (numeric)
            <select value={spec.y} onChange={set('y')}>
              <option value="">— (count)</option>
              {numericCols.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
        )}
        {['grouped_bar', 'stacked_bar', 'scatter'].includes(spec.chart_type) && (
          <label>Group by
            <select value={spec.group} onChange={set('group')}>
              <option value="">—</option>
              {anyCols.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
        )}
        {spec.y && (
          <label>Aggregation
            <select value={spec.agg} onChange={set('agg')}>
              {['sum', 'mean', 'count', 'min', 'max', 'median'].map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </label>
        )}
        {spec.chart_type === 'histogram' && (
          <label>Bins
            <input type="number" min="2" max="100" value={spec.bins} onChange={set('bins')} />
          </label>
        )}
        <label>Filter (e.g. <code>Geography=France</code>)
          <input type="text" placeholder="optional" value={spec.filter} onChange={set('filter')} />
        </label>
        <label>Title
          <input type="text" placeholder="auto-generated if empty" value={spec.title} onChange={set('title')} />
        </label>
        <button className="btn btn-primary" onClick={generate} disabled={busy}>
          {busy ? 'Building…' : 'Generate chart'}
        </button>
      </div>

      {error && <div className="alert-error">{error}</div>}

      {result && (
        <ChartCard
          title={result.spec.title}
          rationale={result.ok ? `Manual chart · ${result.spec.chart_type}` : null}
          option={result.ok ? result.option : null}
          error={result.ok ? null : result.error}
          functionsUsed={result.functions_used}
        />
      )}
    </div>
  )
}
