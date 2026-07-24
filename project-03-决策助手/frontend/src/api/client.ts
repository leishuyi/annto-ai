const BASE = '/api/v1'
export async function request<T>(url: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${url}`, { headers: { 'Content-Type': 'application/json' }, ...opts })
  return r.json()
}
