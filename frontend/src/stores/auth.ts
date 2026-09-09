import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import { clearTokens, getAccessToken } from '@/api/client'
import type { User } from '@/types'
import { isAdminRole, isStaffRole, isSupervisorOrAdminRole } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const initialized = ref(false)

  const isAuthenticated = computed(() => !!user.value && !!getAccessToken())
  const isStaff = computed(() => isStaffRole(user.value?.role))
  const isCustomer = computed(() => user.value?.role === 'customer')
  const isAdmin = computed(() => isAdminRole(user.value?.role))
  const isSupervisorOrAdmin = computed(() => isSupervisorOrAdminRole(user.value?.role))

  function homePathFor(role: User['role'] | undefined): string {
    if (!role) return '/login'
    if (role === 'customer') return '/tickets'
    if (role === 'supervisor' || role === 'admin') return '/admin'
    return '/agent/queue'
  }

  async function login(username: string, password: string, company: string): Promise<User> {
    loading.value = true
    try {
      await authApi.login(username, password, company)
      user.value = await authApi.fetchMe()
      return user.value
    } finally {
      loading.value = false
    }
  }

  async function bootstrap(): Promise<void> {
    if (initialized.value) return
    if (!getAccessToken()) {
      initialized.value = true
      return
    }
    loading.value = true
    try {
      user.value = await Promise.race([
        authApi.fetchMe(),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('Auth bootstrap timed out')), 8000),
        ),
      ])
    } catch {
      clearTokens()
      user.value = null
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  function logout(): void {
    authApi.logout()
    user.value = null
  }

  return {
    user,
    loading,
    initialized,
    isAuthenticated,
    isStaff,
    isCustomer,
    isAdmin,
    isSupervisorOrAdmin,
    homePathFor,
    login,
    bootstrap,
    logout,
  }
})
