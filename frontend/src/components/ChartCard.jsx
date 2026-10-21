import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

export default function ChartCard({ title, rationale, option, error, functionsUsed, onExport }) {
  const ref = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!ref.current || !option) return
    if (!chartRef.current) chartRef.current = echarts.init(ref.current)
    chartRef.current.setOption(option, true)
    chartRef.current.resize()
    const onResize = () => chartRef.current?.resize()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [option])

  const exportPng = () => {
    if (!chartRef.current) return
    const url = chartRef.current.getDataURL({ pixelRatio: 2, backgroundColor: '#fff' })
    const a = document.createElement('a')
    a.href = url
    a.download = `${(title || 'chart').replace(/[^\w-]+/g, '_')}.png`
    a.click()
  }

  return (
    <div className="chart-card">
      <div className="chart-card-head">
        <h3>{title}</h3>
        <button className="btn btn-ghost" onClick={exportPng} disabled={!option}>PNG</button>
      </div>
      {rationale && <p className="rationale">{rationale}</p>}
      {error ? (
        <div className="chart-error">Chart error: {error}</div>
      ) : (
        <div ref={ref} className="chart-body" />
      )}
      {functionsUsed?.length > 0 && (
        <p className="functions-used">Processing: {functionsUsed.join(', ')}</p>
      )}
    </div>
  )
}
