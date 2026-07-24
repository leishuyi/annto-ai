import type { Ticket, TicketCreate, AgentTrace, ReviewRequest, ReviewResponse } from '../types'

const BASE = '/api/v1'
export interface PageResult<T> { total: number; page: number; page_size: number; items: T[] }

async function request<T>(url: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${url}`, { headers: { 'Content-Type': 'application/json' }, ...opts })
  const body = await r.json()
  if (body && typeof body === 'object' && 'code' in body && body.code !== 0) throw new Error(body.message)
  return body as T
}

export const api = {
  getTickets: (p?: { page?: number; page_size?: number }) => {
    const q = new URLSearchParams()
    if (p?.page) q.set('page', String(p.page))
    if (p?.page_size) q.set('page_size', String(p.page_size))
    return request<PageResult<Ticket>>(`/tickets?${q}`)
  },
  getTicket: (id: number) => request<Ticket>(`/tickets/${id}`),
  createTicket: (d: TicketCreate) => request<Ticket>('/tickets', { method: 'POST', body: JSON.stringify(d) }),
  runAgents: (id: number) => request<{ message: string }>(`/${id}/run`, { method: 'POST' }),
  getTraces: (id: number) => request<AgentTrace[]>(`/${id}/traces`),
  getReview: (id: number) => request<ReviewResponse[]>(`/${id}/review`),
  submitReview: (id: number, d: ReviewRequest) => request<ReviewResponse>(`/${id}/review`, { method: 'POST', body: JSON.stringify(d) }),
}
