import { useEffect, useState } from 'react'
import { api, type Provider } from '../api'
import { Badge, formatTime } from '../components'

const KIND_LABELS: Record<string, string> = {
  anthropic: 'Anthropic (Claude)',
  openai: 'OpenAI (GPT)',
  google: 'Google (Gemini)',
  custom: 'Custom (OpenAI-compatible)',
}

export default function Settings() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [error, setError] = useState('')
  const [kind, setKind] = useState('anthropic')
  const [name, setName] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => api.listProviders().then(setProviders).catch((e) => setError(e.message))
  useEffect(() => {
    load()
  }, [])

  const add = async () => {
    setBusy(true)
    setError('')
    try {
      await api.createProvider({
        kind,
        name: name || KIND_LABELS[kind],
        api_key: apiKey,
        base_url: baseUrl || null,
      })
      setName('')
      setApiKey('')
      setBaseUrl('')
      await load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const verify = async (id: number) => {
    try {
      await api.verifyProvider(id)
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const remove = async (id: number) => {
    try {
      await api.deleteProvider(id)
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div>
      <h1>Settings</h1>

      <div className="panel">
        <h2>Link a model provider</h2>
        <p className="muted">
          Add an API key for the provider you want scans to use. Keys are encrypted at rest and
          only handed to the vvaharness process as environment variables. Google is consumed
          through Gemini's OpenAI-compatible endpoint. Custom lets you point at any
          OpenAI-compatible endpoint (Ollama, Groq, OpenRouter, Hugging Face router, …) —
          give its base URL, e.g. http://localhost:11434/v1 for Ollama.
        </p>
        <div className="row">
          <div>
            <label>Provider</label>
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="openai">OpenAI (GPT)</option>
              <option value="google">Google (Gemini)</option>
              <option value="custom">Custom (OpenAI-compatible)</option>
            </select>
          </div>
          <div>
            <label>Display name (optional)</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder={KIND_LABELS[kind]} />
          </div>
          <div>
            <label>{kind === 'custom' ? 'API key (optional)' : 'API key'}</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={kind === 'custom' ? 'leave empty if not needed' : 'sk-…'}
            />
          </div>
          <div>
            <label>{kind === 'custom' ? 'Base URL (required)' : 'Base URL (optional, for gateways)'}</label>
            <input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder={kind === 'custom' ? 'http://localhost:11434/v1' : 'default'}
            />
          </div>
          <div style={{ flex: '0 0 auto' }}>
            <button onClick={add} disabled={busy || (kind === 'custom' ? !baseUrl.trim() : !apiKey.trim())}>
              {busy ? 'Verifying…' : 'Link provider'}
            </button>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      <div className="panel">
        <h2>Linked providers</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Provider</th>
              <th>Status</th>
              <th>Last verified</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{KIND_LABELS[p.kind] ?? p.kind}</td>
                <td>
                  <Badge value={p.status} />
                </td>
                <td className="muted">{formatTime(p.last_verified_at)}</td>
                <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <button className="secondary small" onClick={() => verify(p.id)}>
                    Re-verify
                  </button>{' '}
                  <button className="danger small" onClick={() => remove(p.id)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {providers.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No providers linked yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
