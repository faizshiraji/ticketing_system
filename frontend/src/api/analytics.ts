import { api } from './client'
import type { AnalyticsReport, DashboardSummary } from '@/types'

export async function fetchDashboardSummary(opts?: {
  company?: number
  date_from?: string
  date_to?: string
  days?: number
}): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>('/api/analytics/dashboard-summary/', {
    params: {
      company: opts?.company || undefined,
      date_from: opts?.date_from || undefined,
      date_to: opts?.date_to || undefined,
      days: opts?.days || undefined,
    },
  })
  return data
}

export async function fetchReports(opts?: {
  company?: number
  days?: number
  date_from?: string
  date_to?: string
}): Promise<AnalyticsReport> {
  const { data } = await api.get<AnalyticsReport>('/api/analytics/reports/', {
    params: {
      company: opts?.company || undefined,
      days: opts?.days || undefined,
      date_from: opts?.date_from || undefined,
      date_to: opts?.date_to || undefined,
    },
  })
  return data
}
