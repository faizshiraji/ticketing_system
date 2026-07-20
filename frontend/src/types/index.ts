export type UserRole = 'customer' | 'agent' | 'supervisor' | 'admin'

export type TicketStatus =
  | 'open'
  | 'in_progress'
  | 'on_hold'
  | 'resolved'
  | 'closed'
  | 'reopened'

export interface Company {
  id: number
  name: string
  short_code: string
  is_active: boolean
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  company: Company | null
  phone: string
}

export interface Category {
  id: number
  name: string
  is_active: boolean
}

export interface Priority {
  id: number
  name: string
  rank: number
}

export interface SupportLayerBrief {
  id: number
  name: string
  level: number
  is_active?: boolean
}

export interface SupportLayer extends SupportLayerBrief {
  description: string
  is_active: boolean
  agents: User[]
  agent_ids?: number[]
}

export type MovementType = 'assign' | 'escalate_next' | 'escalate_agent' | 'reassign'

export interface TicketMovement {
  id: number
  actor: User | null
  movement_type: MovementType
  from_agent: User | null
  to_agent: User | null
  from_layer: SupportLayerBrief | null
  to_layer: SupportLayerBrief | null
  reason: string
  created_at: string
}

export interface StaffAgent extends User {
  support_layers: SupportLayerBrief[]
}

export interface TicketListItem {
  id: number
  subject: string
  company: Company
  category: Category
  priority: Priority
  support_layer: SupportLayerBrief | null
  status: TicketStatus
  assigned_agent: number | null
  created_at: string
  resolution_due_at: string | null
  is_sla_breached: boolean
}

export interface TicketAttachment {
  id: number
  file: string
  url?: string
  uploaded_by: number
  uploaded_at: string
}

export interface TicketComment {
  id: number
  ticket: number
  author: User
  body: string
  is_internal: boolean
  created_at: string
  attachments?: TicketAttachment[]
}

export interface TicketActivity {
  id: number
  actor: User | null
  status_from: string
  status_to: string
  note: string
  created_at: string
}

export interface TicketDetail extends TicketListItem {
  description: string
  requester: User
  first_response_due_at: string | null
  first_responded_at: string | null
  resolved_at: string | null
  attachments?: TicketAttachment[]
  comments: TicketComment[]
  activity_log: TicketActivity[]
  movements: TicketMovement[]
}

export interface TicketCreatePayload {
  subject: string
  description: string
  category: number
  priority: number
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface TokenPair {
  access: string
  refresh: string
}

export interface DashboardSummary {
  generated_at: string
  by_status: Record<string, number>
  by_category: { category__name: string | null; count: number }[]
  avg_resolution_seconds: number | null
  currently_open: number
  currently_sla_breached: number
  agent_workload: {
    assigned_agent__id: number
    assigned_agent__first_name: string
    assigned_agent__last_name: string
    open_tickets: number
  }[]
}

export const TICKET_STATUSES: { value: TicketStatus; label: string }[] = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'on_hold', label: 'On hold' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
  { value: 'reopened', label: 'Reopened' },
]

export function isStaffRole(role: UserRole | undefined | null): boolean {
  return role === 'agent' || role === 'supervisor' || role === 'admin'
}

export function isSupervisorOrAdminRole(role: UserRole | undefined | null): boolean {
  return role === 'supervisor' || role === 'admin'
}

export function isAdminRole(role: UserRole | undefined | null): boolean {
  return role === 'admin'
}

export function displayName(user: Pick<User, 'first_name' | 'last_name' | 'username'>): string {
  const full = `${user.first_name} ${user.last_name}`.trim()
  return full || user.username
}

export interface AdminUser extends User {
  is_active: boolean
}

export interface CompanyWrite {
  name: string
  short_code: string
  is_active: boolean
}

export interface UserWrite {
  username: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  company_id: number | null
  phone: string
  is_active: boolean
  password?: string
}

export interface DayCount {
  date: string
  count: number
}

export interface BreachedTicket {
  id: number
  subject: string
  company: Pick<Company, 'id' | 'name' | 'short_code'>
  status: TicketStatus
  resolution_due_at: string | null
}

export interface AnalyticsReport {
  generated_at: string
  days: number
  company: number | null
  created_in_period: number
  resolved_in_period: number
  tickets_created_by_day: DayCount[]
  tickets_resolved_by_day: DayCount[]
  open_sla_breached: BreachedTicket[]
}

export const USER_ROLES: { value: UserRole; label: string }[] = [
  { value: 'customer', label: 'Customer' },
  { value: 'agent', label: 'Agent' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'admin', label: 'Admin' },
]

export const MOVEMENT_LABELS: Record<MovementType, string> = {
  assign: 'Assigned',
  escalate_next: 'Escalated to next layer',
  escalate_agent: 'Escalated to agent',
  reassign: 'Reassigned',
}
