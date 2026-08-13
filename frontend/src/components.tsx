const STATUS_COLOR: Record<string, string> = {
  succeeded: 'green',
  verified: 'green',
  fixed: 'green',
  failed: 'red',
  invalid: 'red',
  error: 'red',
  canceled: 'amber',
  warning: 'amber',
  confirmed: 'red',
  scanning: 'blue',
  estimating: 'blue',
  cloning: 'blue',
  ingesting: 'blue',
  open: 'blue',
}

export function Badge({ value }: { value: string }) {
  const color = STATUS_COLOR[value] ?? ''
  return <span className={`badge ${color}`}>{value.replace(/_/g, ' ')}</span>
}

export function BarChart({ data, color }: { data: Record<string, number>; color?: string }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1])
  const max = Math.max(1, ...entries.map(([, v]) => v))
  if (entries.length === 0) return <div className="muted">No data yet</div>
  return (
    <div>
      {entries.map(([name, count]) => (
        <div className="bar-row" key={name}>
          <div className="name">{name.replace(/_/g, ' ')}</div>
          <div className="bar">
            <div style={{ width: `${(count / max) * 100}%`, background: color }} />
          </div>
          <div className="count">{count}</div>
        </div>
      ))}
    </div>
  )
}

export function formatTime(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

export function duration(start: string | null, end: string | null): string {
  if (!start) return '—'
  const ms = (end ? new Date(end).getTime() : Date.now()) - new Date(start).getTime()
  const s = Math.max(0, Math.round(ms / 1000))
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ${s % 60}s`
  return `${Math.floor(m / 60)}h ${m % 60}m`
}
