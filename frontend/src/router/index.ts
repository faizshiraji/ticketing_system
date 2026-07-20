import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      redirect: () => {
        const auth = useAuthStore()
        if (!auth.isAuthenticated) return '/login'
        return auth.homePathFor(auth.user?.role)
      },
    },
    {
      path: '/tickets',
      name: 'customer-tickets',
      component: () => import('@/views/customer/TicketListView.vue'),
      meta: { roles: ['customer'] },
    },
    {
      path: '/tickets/new',
      name: 'customer-ticket-create',
      component: () => import('@/views/customer/TicketCreateView.vue'),
      meta: { roles: ['customer'] },
    },
    {
      path: '/tickets/:id',
      name: 'customer-ticket-detail',
      component: () => import('@/views/customer/TicketDetailView.vue'),
      meta: { roles: ['customer'] },
    },
    {
      path: '/agent/queue',
      name: 'agent-queue',
      component: () => import('@/views/agent/TicketQueueView.vue'),
      meta: { roles: ['agent', 'supervisor', 'admin'] },
    },
    {
      path: '/agent/tickets/:id',
      name: 'agent-ticket-detail',
      component: () => import('@/views/agent/TicketDetailView.vue'),
      meta: { roles: ['agent', 'supervisor', 'admin'] },
    },
    {
      path: '/agent/dashboard',
      name: 'agent-dashboard',
      component: () => import('@/views/agent/DashboardView.vue'),
      meta: { roles: ['agent', 'supervisor', 'admin'] },
    },
    {
      path: '/admin',
      name: 'admin-home',
      component: () => import('@/views/admin/AdminHomeView.vue'),
      meta: { roles: ['supervisor', 'admin'] },
    },
    {
      path: '/admin/companies',
      name: 'admin-companies',
      component: () => import('@/views/admin/CompaniesView.vue'),
      meta: { roles: ['supervisor', 'admin'] },
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/views/admin/UsersView.vue'),
      meta: { roles: ['supervisor', 'admin'] },
    },
    {
      path: '/admin/categories',
      name: 'admin-categories',
      component: () => import('@/views/admin/CategoriesView.vue'),
      meta: { roles: ['supervisor', 'admin'] },
    },
    {
      path: '/admin/priorities',
      name: 'admin-priorities',
      component: () => import('@/views/admin/PrioritiesView.vue'),
      meta: { roles: ['supervisor', 'admin'] },
    },
    {
      path: '/admin/support-layers',
      name: 'admin-support-layers',
      component: () => import('@/views/admin/SupportLayersView.vue'),
      meta: { roles: ['supervisor', 'admin'] },
    },
    {
      path: '/admin/analytics',
      name: 'admin-analytics',
      component: () => import('@/views/admin/AnalyticsView.vue'),
      meta: { roles: ['supervisor', 'admin'] },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.initialized) {
    await auth.bootstrap()
  }

  if (to.meta.public) {
    if (auth.isAuthenticated && to.name === 'login') {
      return auth.homePathFor(auth.user?.role)
    }
    return true
  }

  if (!auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  const roles = to.meta.roles as string[] | undefined
  if (roles && auth.user && !roles.includes(auth.user.role)) {
    return auth.homePathFor(auth.user.role)
  }

  return true
})

export default router
