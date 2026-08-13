export interface Provider {
  id: number
  kind: 'anthropic' | 'openai' | 'google'
  name: string
  base_url: string | null
  status: 'unverified' | 'verified' | 'invalid'
  last_verified_at: string | null
  created_at: string
}

export interface ModelInfo {
  id: string
  display_name: string | null
}

export interface Target {
  id: number
  name: string
  git_url: string | null
  local_path: string | null
  created_at: string
}

export interface Scan {
  id: number
  target_id: number
  provider_id: number
  model_id: string
  application_id: string
  status: string
  error: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface ScanDetail extends Scan {
  estimate_output: string | null
  report_path: string | null
  sarif_path: string | null
}

export interface Finding {
  id: number
  scan_id: number
  rule_id: string | null
  title: string
  message: string | null
  severity: string
  cwe: string | null
  file: string | null
  line: number | null
  state: string
  created_at: string
}

export interface Metrics {
  total_scans: number
  scans_by_status: Record<string, number>
  total_findings: number
  findings_by_severity: Record<string, number>
  findings_by_state: Record<string, number>
  top_cwes: { cwe: string; count: number }[]
  recent_scans: Scan[]
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  const contentType = res.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) return res.json() as Promise<T>
  return res.text() as Promise<T>
}

export const api = {
  listProviders: () => request<Provider[]>('/api/providers'),
  createProvider: (body: { kind: string; name: string; api_key: string; base_url?: string | null }) =>
    request<Provider>('/api/providers', { method: 'POST', body: JSON.stringify(body) }),
  verifyProvider: (id: number) => request<Provider>(`/api/providers/${id}/verify`, { method: 'POST' }),
  deleteProvider: (id: number) => request<{ ok: boolean }>(`/api/providers/${id}`, { method: 'DELETE' }),
  listModels: (providerId: number) => request<ModelInfo[]>(`/api/providers/${providerId}/models`),

  listTargets: () => request<Target[]>('/api/targets'),
  createTarget: (body: { name: string; git_url?: string | null; local_path?: string | null }) =>
    request<Target>('/api/targets', { method: 'POST', body: JSON.stringify(body) }),
  deleteTarget: (id: number) => request<{ ok: boolean }>(`/api/targets/${id}`, { method: 'DELETE' }),

  listScans: () => request<Scan[]>('/api/scans'),
  createScan: (body: { target_id: number; provider_id: number; model_id: string; application_id?: string }) =>
    request<Scan>('/api/scans', { method: 'POST', body: JSON.stringify(body) }),
  getScan: (id: number) => request<ScanDetail>(`/api/scans/${id}`),
  getScanLog: (id: number) => request<string>(`/api/scans/${id}/log`),
  getScanReport: (id: number) => request<string>(`/api/scans/${id}/report`),
  cancelScan: (id: number) => request<Scan>(`/api/scans/${id}/cancel`, { method: 'POST' }),

  listFindings: (params?: { scan_id?: number; state?: string; severity?: string }) => {
    const qs = new URLSearchParams()
    if (params?.scan_id != null) qs.set('scan_id', String(params.scan_id))
    if (params?.state) qs.set('state', params.state)
    if (params?.severity) qs.set('severity', params.severity)
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return request<Finding[]>(`/api/findings${suffix}`)
  },
  updateFindingState: (id: number, state: string) =>
    request<Finding>(`/api/findings/${id}`, { method: 'PATCH', body: JSON.stringify({ state }) }),

  getMetrics: () => request<Metrics>('/api/metrics'),
}
