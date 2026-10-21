import { useEffect, useState } from 'react'
import { api } from './api.js'
import UploadPage from './pages/UploadPage.jsx'
import AutoVizPage from './pages/AutoVizPage.jsx'
import ManualPage from './pages/ManualPage.jsx'

const TABS = [
  { id: 'dataset', label: '1 · Dataset' },
  { id: 'auto', label: '2 · Auto-visualise' },
  { id: 'manual', label: '3 · Manual builder' },
]

export default function App() {
  const [tab, setTab] = useState('dataset')
  const [dataset, setDataset] = useState(null)
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
  }, [])

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">BankViz</span>
          <span className="tagline">Local LLM-powered exploration for retail-bank datasets — no data leaves this machine</span>
        </div>
        <div className={`health ${health?.ollama.reachable ? 'ok' : health ? 'warn' : 'unknown'}`}>
          {health
            ? health.ollama.reachable
              ? `LLM ready · ${health.ollama.model}`
              : 'Degraded mode · LLM offline'
            : 'Backend offline'}
        </div>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? 'active' : ''} ${(t.id !== 'dataset' && !dataset) ? 'disabled' : ''}`}
            onClick={() => (t.id === 'dataset' || dataset) && setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
        {dataset && (
          <span className="dataset-chip">
            {dataset.filename} · {dataset.meta?.n_rows.toLocaleString()} rows
            <button className="chip-x" title="Remove dataset" onClick={() => { setDataset(null); setTab('dataset') }}>×</button>
          </span>
        )}
      </nav>

      <main>
        {tab === 'dataset' && <UploadPage dataset={dataset} onUploaded={setDataset} health={health} />}
        {tab === 'auto' && <AutoVizPage dataset={dataset} />}
        {tab === 'manual' && <ManualPage dataset={dataset} />}
      </main>

      <footer className="footer">
        BankViz — MSc IT+ Development Project · All processing (pandas, LLM, rendering) runs locally · No login, no telemetry
      </footer>
    </div>
  )
}
