import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ModelInfo, type Provider, type Scan, type Target } from '../api'
import { Badge, duration, formatTime } from '../components'

export default function Scans() {
  const [scans, setScans] = useState<Scan[]>([])
  const [providers, setProviders] = useState<Provider[]>([])
  const [targets, setTargets] = useState<Target[]>([])
  const [models, setModels] = useState<ModelInfo[]>([])
  const [modelsError, setModelsError] = useState('')
  const [error, setError] = useState('')

  const [targetId, setTargetId] = useState('')
  const [providerId, setProviderId] = useState('')
  const [modelId, setModelId] = useState('')
  const [appId, setAppId] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => api.listScans().then(setScans).catch((e) => setError(e.message))

  useEffect(() => {
    load()
    api.listProviders().then(setProviders).catch(() => {})
    api.listTargets().then(setTargets).catch(() => {})
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    setModels([])
    setModelId('')
    setModelsError('')
    if (!providerId) return
    api
      .listModels(Number(providerId))
      .then(setModels)
      .catch((e) => setModelsError(e.message))
  }, [providerId])

  const start = async () => {
    setBusy(true)
    setError('')
    try {
      await api.createScan({
        target_id: Number(targetId),
        provider_id: Number(providerId),
        model_id: modelId,
        application_id: appId || undefined,
      })
      setAppId('')
      await load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const targetName = (id: number) => targets.find((t) => t.id === id)?.name ?? `#${id}`
  const providerName = (id: number) => providers.find((p) => p.id === id)?.name ?? `#${id}`

  return (
    <div>
      <h1>Scans</h1>

      <div className="panel">
        <h2>Start a scan</h2>
        <p className="muted">
          Runs vvaharness detection (S1–S9, no source edits) with your selected provider and
          model. Findings are LLM-generated triage candidates, not confirmed vulnerabilities.
        </p>
        <div className="row">
          <div>
            <label>Target</label>
            <select value={targetId} onChange={(e) => setTargetId(e.target.value)}>
              <option value="">Select target…</option>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Provider</label>
            <select value={providerId} onChange={(e) => setProviderId(e.target.value)}>
              <option value="">Select provider…</option>
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.kind})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Model</label>
            <select value={modelId} onChange={(e) => setModelId(e.target.value)} disabled={!providerId}>
              <option value="">{models.length ? 'Select model…' : 'Pick a provider first'}</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name ? `${m.display_name} (${m.id})` : m.id}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Application ID (optional)</label>
            <input value={appId} onChange={(e) => setAppId(e.target.value)} placeholder="auto" />
          </div>
          <div style={{ flex: '0 0 auto' }}>
            <button onClick={start} disabled={busy || !targetId || !providerId || !modelId}>
              {busy ? 'Starting…' : 'Start scan'}
            </button>
          </div>
        </div>
        {modelsError && <div className="error">Could not list models: {modelsError}</div>}
        {error && <div className="error">{error}</div>}
      </div>

      <div className="panel">
        <h2>All scans</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Target</th>
              <th>Provider</th>
              <th>Model</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {scans.map((s) => (
              <tr key={s.id}>
                <td>
                  <Link to={`/scans/${s.id}`}>#{s.id}</Link>
                </td>
                <td>{targetName(s.target_id)}</td>
                <td>{providerName(s.provider_id)}</td>
                <td className="mono">{s.model_id}</td>
                <td>
                  <Badge value={s.status} />
                </td>
                <td className="muted">{duration(s.started_at, s.finished_at)}</td>
                <td className="muted">{formatTime(s.created_at)}</td>
              </tr>
            ))}
            {scans.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">
                  No scans yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
