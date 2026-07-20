import { api } from './client'
import type { AnalyticsReport, DashboardSummary } from '@/types'

export async function fetchDashboardSummary(companyId?: number): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>('/api/analytics/dashboard-summary/', {
    params: companyId ? { company: companyId } : undefined,
  })
  return data
}

export async function fetchReports(opts?: {
  company?: number
  days?: number
}): Promise<AnalyticsReport> {
  const { data } = await api.get<AnalyticsReport>('/api/analytics/reports/', {
    params: {
      company: opts?.company || undefined,
      days: opts?.days || undefined,
    },
  })
  return data
}
