import { useEffect, useState } from 'react'
import { api, type Target } from '../api'
import { formatTime } from '../components'

export default function Targets() {
  const [targets, setTargets] = useState<Target[]>([])
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [gitUrl, setGitUrl] = useState('')
  const [localPath, setLocalPath] = useState('')

  const load = () => api.listTargets().then(setTargets).catch((e) => setError(e.message))
  useEffect(() => {
    load()
  }, [])

  const add = async () => {
    setError('')
    try {
      await api.createTarget({
        name,
        git_url: gitUrl || null,
        local_path: localPath || null,
      })
      setName('')
      setGitUrl('')
      setLocalPath('')
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const remove = async (id: number) => {
    try {
      await api.deleteTarget(id)
      await load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div>
      <h1>Targets</h1>
      <div className="panel">
        <h2>Add a target repository</h2>
        <p className="muted">
          Provide a git URL (cloned fresh for each scan) or a local path on the server. Only scan
          code you are authorized to scan.
        </p>
        <div className="row">
          <div>
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="my-service" />
          </div>
          <div>
            <label>Git URL</label>
            <input
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              placeholder="https://github.com/org/repo.git"
            />
          </div>
          <div>
            <label>…or local path</label>
            <input
              value={localPath}
              onChange={(e) => setLocalPath(e.target.value)}
              placeholder="/path/on/server"
            />
          </div>
          <div style={{ flex: '0 0 auto' }}>
            <button onClick={add} disabled={!name.trim() || (!gitUrl.trim() && !localPath.trim())}>
              Add target
            </button>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      <div className="panel">
        <h2>Registered targets</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Source</th>
              <th>Added</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {targets.map((t) => (
              <tr key={t.id}>
                <td>{t.name}</td>
                <td className="mono">{t.git_url ?? t.local_path}</td>
                <td className="muted">{formatTime(t.created_at)}</td>
                <td style={{ textAlign: 'right' }}>
                  <button className="danger small" onClick={() => remove(t.id)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {targets.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No targets yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
