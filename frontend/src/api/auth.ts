import { api, setTokens, clearTokens } from './client'
import type { TokenPair, User } from '@/types'

export async function login(username: string, password: string): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>('/api/auth/token/', { username, password })
  setTokens(data.access, data.refresh)
  return data
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>('/api/accounts/me/')
  return data
}

export function logout(): void {
  clearTokens()
}
