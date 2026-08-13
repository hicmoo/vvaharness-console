import { useCallback, useEffect, useState } from 'react'
import { api, type Finding } from '../api'
import { Badge } from '../components'

const STATES = ['open', 'confirmed', 'false_positive', 'accepted_risk', 'fixed']

export function FindingsTable({
  findings,
  onChanged,
}: {
  findings: Finding[]
  onChanged: () => void
}) {
  const [error, setError] = useState('')

  const setState = async (id: number, state: string) => {
    try {
      await api.updateFindingState(id, state)
      onChanged()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Finding</th>
            <th>CWE</th>
            <th>Location</th>
            <th>Scan</th>
            <th>Triage</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f) => (
            <tr key={f.id}>
              <td>
                <Badge value={f.severity} />
              </td>
              <td>
                <div>{f.title}</div>
                {f.message && f.message !== f.title && (
                  <div className="muted" style={{ marginTop: 4, fontSize: 12.5 }}>
                    {f.message.length > 300 ? `${f.message.slice(0, 300)}…` : f.message}
                  </div>
                )}
              </td>
              <td className="mono">{f.cwe ?? '—'}</td>
              <td className="mono">
                {f.file ?? '—'}
                {f.line != null ? `:${f.line}` : ''}
              </td>
              <td>#{f.scan_id}</td>
              <td>
                <select
                  value={f.state}
                  onChange={(e) => setState(f.id, e.target.value)}
                  style={{ marginBottom: 0, width: 150 }}
                >
                  {STATES.map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
          {findings.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No findings.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default function Findings() {
  const [findings, setFindings] = useState<Finding[]>([])
  const [state, setState] = useState('')
  const [severity, setSeverity] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(() => {
    api
      .listFindings({ state: state || undefined, severity: severity || undefined })
      .then(setFindings)
      .catch((e) => setError(e.message))
  }, [state, severity])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div>
      <h1>Findings</h1>
      <div className="panel">
        <div className="row">
          <div>
            <label>Triage state</label>
            <select value={state} onChange={(e) => setState(e.target.value)}>
              <option value="">All states</option>
              {STATES.map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Severity</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="">All severities</option>
              <option value="error">error</option>
              <option value="warning">warning</option>
              <option value="note">note</option>
              <option value="none">none</option>
            </select>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        <FindingsTable findings={findings} onChanged={load} />
        <p className="muted">
          Findings are LLM-generated triage candidates from vvaharness — not confirmed
          vulnerabilities.
        </p>
      </div>
    </div>
  )
}
