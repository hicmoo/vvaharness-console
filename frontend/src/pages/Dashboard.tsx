import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Metrics } from '../api'
import { Badge, BarChart, formatTime } from '../components'

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = () => api.getMetrics().then(setMetrics).catch((e) => setError(e.message))
    load()
    const t = setInterval(load, 8000)
    return () => clearInterval(t)
  }, [])

  if (error) return <div className="error">{error}</div>
  if (!metrics) return <div className="muted">Loading…</div>

  const openCount = metrics.findings_by_state['open'] ?? 0
  const confirmedCount = metrics.findings_by_state['confirmed'] ?? 0

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="cards">
        <div className="card">
          <div className="label">Total scans</div>
          <div className="value">{metrics.total_scans}</div>
        </div>
        <div className="card">
          <div className="label">Total findings</div>
          <div className="value">{metrics.total_findings}</div>
        </div>
        <div className="card">
          <div className="label">Open findings</div>
          <div className="value">{openCount}</div>
        </div>
        <div className="card">
          <div className="label">Confirmed</div>
          <div className="value">{confirmedCount}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h2>Findings by severity</h2>
          <BarChart data={metrics.findings_by_severity} color="var(--red)" />
        </div>
        <div className="panel">
          <h2>Findings by triage state</h2>
          <BarChart data={metrics.findings_by_state} color="var(--amber)" />
        </div>
        <div className="panel">
          <h2>Top CWEs</h2>
          <BarChart
            data={Object.fromEntries(metrics.top_cwes.map((c) => [c.cwe, c.count]))}
          />
        </div>
        <div className="panel">
          <h2>Scans by status</h2>
          <BarChart data={metrics.scans_by_status} color="var(--green)" />
        </div>
      </div>

      <div className="panel">
        <h2>Recent scans</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Model</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {metrics.recent_scans.map((s) => (
              <tr key={s.id}>
                <td>
                  <Link to={`/scans/${s.id}`}>#{s.id}</Link>
                </td>
                <td className="mono">{s.model_id}</td>
                <td>
                  <Badge value={s.status} />
                </td>
                <td className="muted">{formatTime(s.created_at)}</td>
              </tr>
            ))}
            {metrics.recent_scans.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No scans yet — start one from the Scans page.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
