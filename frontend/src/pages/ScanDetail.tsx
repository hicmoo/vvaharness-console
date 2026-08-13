import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Finding, type ScanDetail } from '../api'
import { Badge, duration, formatTime } from '../components'
import { FindingsTable } from './Findings'

const RUNNING = new Set(['queued', 'cloning', 'estimating', 'scanning', 'ingesting'])

export default function ScanDetailPage() {
  const { id } = useParams()
  const scanId = Number(id)
  const [scan, setScan] = useState<ScanDetail | null>(null)
  const [log, setLog] = useState('')
  const [report, setReport] = useState('')
  const [findings, setFindings] = useState<Finding[]>([])
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'log' | 'report' | 'estimate'>('log')

  const load = useCallback(async () => {
    try {
      const s = await api.getScan(scanId)
      setScan(s)
      setLog(await api.getScanLog(scanId))
      if (s.status === 'succeeded') {
        setFindings(await api.listFindings({ scan_id: scanId }))
        if (s.report_path) {
          api.getScanReport(scanId).then(setReport).catch(() => {})
        }
      }
    } catch (e) {
      setError((e as Error).message)
    }
  }, [scanId])

  useEffect(() => {
    load()
    const t = setInterval(() => {
      setScan((current) => {
        if (!current || RUNNING.has(current.status)) load()
        return current
      })
    }, 4000)
    return () => clearInterval(t)
  }, [load])

  const cancel = async () => {
    try {
      await api.cancelScan(scanId)
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (error && !scan) return <div className="error">{error}</div>
  if (!scan) return <div className="muted">Loading…</div>

  return (
    <div>
      <h1>
        Scan #{scan.id} <Badge value={scan.status} />
      </h1>
      <div className="panel">
        <table>
          <tbody>
            <tr>
              <td className="muted">Model</td>
              <td className="mono">{scan.model_id}</td>
              <td className="muted">Application ID</td>
              <td className="mono">{scan.application_id}</td>
            </tr>
            <tr>
              <td className="muted">Started</td>
              <td>{formatTime(scan.started_at)}</td>
              <td className="muted">Duration</td>
              <td>{duration(scan.started_at, scan.finished_at)}</td>
            </tr>
          </tbody>
        </table>
        {scan.error && <div className="error">Error: {scan.error}</div>}
        {RUNNING.has(scan.status) && (
          <div style={{ marginTop: 12 }}>
            <button className="danger small" onClick={cancel}>
              Cancel scan
            </button>
          </div>
        )}
      </div>

      <div className="panel">
        <div style={{ marginBottom: 12 }}>
          <button
            className={tab === 'log' ? 'small' : 'secondary small'}
            onClick={() => setTab('log')}
          >
            Live log
          </button>{' '}
          <button
            className={tab === 'estimate' ? 'small' : 'secondary small'}
            onClick={() => setTab('estimate')}
          >
            Cost estimate
          </button>{' '}
          <button
            className={tab === 'report' ? 'small' : 'secondary small'}
            onClick={() => setTab('report')}
            disabled={!report}
          >
            Report
          </button>
        </div>
        {tab === 'log' && <pre className="log">{log || 'No output yet…'}</pre>}
        {tab === 'estimate' && (
          <pre className="log">{scan.estimate_output || 'No estimate output.'}</pre>
        )}
        {tab === 'report' && <pre className="log">{report}</pre>}
      </div>

      {scan.status === 'succeeded' && (
        <div className="panel">
          <h2>Findings ({findings.length})</h2>
          <FindingsTable findings={findings} onChanged={load} />
          <p className="muted">
            Findings are LLM-generated triage candidates, not confirmed vulnerabilities. Triage
            them in the <Link to="/findings">Findings</Link> view.
          </p>
        </div>
      )}
    </div>
  )
}
