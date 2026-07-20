import { api } from './client'
import type {
  Category,
  Paginated,
  Priority,
  SupportLayer,
  TicketAttachment,
  TicketComment,
  TicketCreatePayload,
  TicketDetail,
  TicketListItem,
  TicketStatus,
} from '@/types'

export interface TicketFilters {
  status?: TicketStatus | ''
  category?: number | ''
  priority?: number | ''
  assigned_agent?: number | ''
  company?: number | ''
  page?: number
}

function toParams(filters: TicketFilters = {}): Record<string, string | number> {
  const params: Record<string, string | number> = {}
  if (filters.status) params.status = filters.status
  if (filters.category) params.category = filters.category
  if (filters.priority) params.priority = filters.priority
  if (filters.assigned_agent) params.assigned_agent = filters.assigned_agent
  if (filters.company) params.company = filters.company
  if (filters.page) params.page = filters.page
  return params
}

export async function listTickets(filters: TicketFilters = {}): Promise<Paginated<TicketListItem>> {
  const { data } = await api.get<Paginated<TicketListItem>>('/api/tickets/', {
    params: toParams(filters),
  })
  return data
}

export async function getTicket(id: number): Promise<TicketDetail> {
  const { data } = await api.get<TicketDetail>(`/api/tickets/${id}/`)
  return data
}

export async function createTicket(payload: TicketCreatePayload): Promise<{ id: number }> {
  const { data } = await api.post<{ id: number }>('/api/tickets/', payload)
  return data
}

export async function updateTicket(
  id: number,
  payload: Partial<{ status: TicketStatus; assigned_agent: number | null }>,
): Promise<TicketDetail> {
  const { data } = await api.patch<TicketDetail>(`/api/tickets/${id}/`, payload)
  return data
}

export async function listComments(ticketId: number): Promise<TicketComment[] | Paginated<TicketComment>> {
  const { data } = await api.get<TicketComment[] | Paginated<TicketComment>>(
    `/api/tickets/${ticketId}/comments/`,
  )
  return data
}

export async function createComment(
  ticketId: number,
  body: string,
  isInternal = false,
  files: File[] = [],
): Promise<TicketComment> {
  if (files.length) {
    const form = new FormData()
    form.append('ticket', String(ticketId))
    form.append('body', body)
    form.append('is_internal', isInternal ? 'true' : 'false')
    for (const file of files) {
      form.append('files', file)
    }
    const { data } = await api.post<TicketComment>(`/api/tickets/${ticketId}/comments/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  }
  const { data } = await api.post<TicketComment>(`/api/tickets/${ticketId}/comments/`, {
    ticket: ticketId,
    body,
    is_internal: isInternal,
  })
  return data
}

export async function uploadTicketAttachment(
  ticketId: number,
  file: File,
): Promise<TicketAttachment> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<TicketAttachment>(`/api/tickets/${ticketId}/attachments/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function listCategories(): Promise<Category[] | Paginated<Category>> {
  const { data } = await api.get<Category[] | Paginated<Category>>('/api/tickets/categories/')
  return data
}

export async function createCategory(payload: { name: string; is_active: boolean }): Promise<Category> {
  const { data } = await api.post<Category>('/api/tickets/categories/', payload)
  return data
}

export async function updateCategory(
  id: number,
  payload: Partial<{ name: string; is_active: boolean }>,
): Promise<Category> {
  const { data } = await api.patch<Category>(`/api/tickets/categories/${id}/`, payload)
  return data
}

export async function deleteCategory(id: number): Promise<void> {
  await api.delete(`/api/tickets/categories/${id}/`)
}

export async function listPriorities(): Promise<Priority[] | Paginated<Priority>> {
  const { data } = await api.get<Priority[] | Paginated<Priority>>('/api/tickets/priorities/')
  return data
}

export async function createPriority(payload: { name: string; rank: number }): Promise<Priority> {
  const { data } = await api.post<Priority>('/api/tickets/priorities/', payload)
  return data
}

export async function updatePriority(
  id: number,
  payload: Partial<{ name: string; rank: number }>,
): Promise<Priority> {
  const { data } = await api.patch<Priority>(`/api/tickets/priorities/${id}/`, payload)
  return data
}

export async function deletePriority(id: number): Promise<void> {
  await api.delete(`/api/tickets/priorities/${id}/`)
}

export async function listSupportLayers(): Promise<SupportLayer[]> {
  const { data } = await api.get<SupportLayer[] | Paginated<SupportLayer>>(
    '/api/tickets/support-layers/',
  )
  return unwrapList(data)
}

export async function createSupportLayer(payload: {
  name: string
  level: number
  description?: string
  is_active: boolean
  agent_ids?: number[]
}): Promise<SupportLayer> {
  const { data } = await api.post<SupportLayer>('/api/tickets/support-layers/', payload)
  return data
}

export async function updateSupportLayer(
  id: number,
  payload: Partial<{
    name: string
    level: number
    description: string
    is_active: boolean
    agent_ids: number[]
  }>,
): Promise<SupportLayer> {
  const { data } = await api.patch<SupportLayer>(`/api/tickets/support-layers/${id}/`, payload)
  return data
}

export async function deleteSupportLayer(id: number): Promise<void> {
  await api.delete(`/api/tickets/support-layers/${id}/`)
}

export async function escalateTicket(
  id: number,
  payload: { mode: 'next' | 'agent'; reason: string; target_agent_id?: number | null },
): Promise<TicketDetail> {
  const { data } = await api.post<TicketDetail>(`/api/tickets/${id}/escalate/`, payload)
  return data
}

export function unwrapList<T>(data: T[] | Paginated<T>): T[] {
  return Array.isArray(data) ? data : data.results
}
