import { api } from './client'
import type { AdminUser, Company, CompanyWrite, Paginated, StaffAgent, UserWrite } from '@/types'
import { unwrapList } from './tickets'

export async function listCompanies(): Promise<Company[]> {
  const { data } = await api.get<Company[] | Paginated<Company>>('/api/accounts/companies/')
  return unwrapList(data)
}

export async function createCompany(payload: CompanyWrite): Promise<Company> {
  const { data } = await api.post<Company>('/api/accounts/companies/', payload)
  return data
}

export async function updateCompany(id: number, payload: Partial<CompanyWrite>): Promise<Company> {
  const { data } = await api.patch<Company>(`/api/accounts/companies/${id}/`, payload)
  return data
}

export async function deleteCompany(id: number): Promise<void> {
  await api.delete(`/api/accounts/companies/${id}/`)
}

export async function listUsers(params?: {
  role?: string
  company?: number
  is_active?: boolean
}): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[] | Paginated<AdminUser>>('/api/accounts/users/', {
    params,
  })
  return unwrapList(data)
}

export async function listStaffAgents(): Promise<StaffAgent[]> {
  const { data } = await api.get<StaffAgent[] | Paginated<StaffAgent>>('/api/accounts/agents/')
  return unwrapList(data)
}

export async function createUser(payload: UserWrite): Promise<AdminUser> {
  const { data } = await api.post<AdminUser>('/api/accounts/users/', payload)
  return data
}

export async function updateUser(id: number, payload: Partial<UserWrite>): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/api/accounts/users/${id}/`, payload)
  return data
}

export async function deleteUser(id: number): Promise<void> {
  await api.delete(`/api/accounts/users/${id}/`)
}
