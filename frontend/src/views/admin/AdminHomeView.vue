<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { displayName } from '@/types'

const auth = useAuthStore()
const { user, isAdmin } = storeToRefs(auth)

const links = computed(() => [
  { to: '/agent/queue', title: 'Ticket queue', desc: 'Triage and update support tickets' },
  { to: '/agent/dashboard', title: 'Ops dashboard', desc: 'Open workload and agent load' },
  { to: '/admin/analytics', title: 'Analytics reports', desc: 'Trends, period totals, SLA breaches' },
  {
    to: '/admin/support-layers',
    title: 'Support layers',
    desc: 'Configure L1/L2/L3 tiers and assign agents',
  },
  { to: '/admin/companies', title: 'Companies', desc: 'CCL, CCDL, and client companies' },
  {
    to: '/admin/users',
    title: 'Users',
    desc: isAdmin.value ? 'Create and manage accounts' : 'Browse accounts (admin can edit)',
  },
  { to: '/admin/categories', title: 'Categories', desc: 'ERP and mobile-app support categories' },
  { to: '/admin/priorities', title: 'Priorities', desc: 'Urgency ranks used for SLA' },
])
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Admin</h1>
        <p>
          Welcome{{ user ? `, ${displayName(user)}` : '' }}. Manage the support desk configuration
          and review operations.
        </p>
      </div>
    </div>

    <div class="hub-grid">
      <RouterLink v-for="link in links" :key="link.to" class="card hub-card" :to="link.to">
        <strong>{{ link.title }}</strong>
        <span>{{ link.desc }}</span>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.hub-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.hub-card {
  padding: 1.25rem;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  transition: border-color 0.12s ease, transform 0.12s ease;
}

.hub-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
  text-decoration: none;
}

.hub-card strong {
  font-size: 1.05rem;
}

.hub-card span {
  color: var(--ink-muted);
  font-size: 0.9rem;
}
</style>
