<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { displayName } from '@/types'

const auth = useAuthStore()
const { user, isStaff, isSupervisorOrAdmin } = storeToRefs(auth)
const router = useRouter()

const isAgentOnly = computed(() => isStaff.value && !isSupervisorOrAdmin.value)

function onLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <span class="mark">CCL</span>
        <div>
          <strong>Support Desk</strong>
          <span class="sub">CCL / CCDL</span>
        </div>
      </div>

      <nav v-if="isSupervisorOrAdmin" class="nav">
        <RouterLink to="/admin">Admin</RouterLink>
        <RouterLink to="/admin/support-layers">Layers</RouterLink>
        <RouterLink to="/agent/queue">Queue</RouterLink>
        <RouterLink to="/agent/dashboard">Dashboard</RouterLink>
        <RouterLink to="/admin/analytics">Analytics</RouterLink>
      </nav>
      <nav v-else-if="isAgentOnly" class="nav">
        <RouterLink to="/agent/queue">Queue</RouterLink>
        <RouterLink to="/agent/dashboard">Dashboard</RouterLink>
      </nav>
      <nav v-else class="nav">
        <RouterLink to="/tickets">My tickets</RouterLink>
        <RouterLink to="/tickets/new">New ticket</RouterLink>
      </nav>

      <div class="user">
        <div class="who">
          <strong>{{ user ? displayName(user) : '' }}</strong>
          <span>{{ user?.role }}{{ user?.company ? ` · ${user.company.short_code}` : '' }}</span>
        </div>
        <button type="button" class="btn btn-ghost" @click="onLogout">Log out</button>
      </div>
    </header>
    <main>
      <slot />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
}

.topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem 1.5rem;
  padding: 0.85rem 1.25rem;
  background: rgba(255, 255, 255, 0.86);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand strong {
  display: block;
  font-size: 0.95rem;
}

.brand .sub {
  font-size: 0.75rem;
  color: var(--ink-muted);
}

.mark {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 8px;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 0.7rem;
  letter-spacing: 0.04em;
}

.nav {
  display: flex;
  gap: 0.25rem;
  flex: 1;
  flex-wrap: wrap;
}

.nav a {
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  color: var(--ink-muted);
  font-weight: 600;
  text-decoration: none;
}

.nav a:hover,
.nav a.router-link-active {
  background: var(--accent-soft);
  color: var(--accent);
}

.user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: auto;
}

.who {
  text-align: right;
  font-size: 0.85rem;
}

.who strong {
  display: block;
}

.who span {
  color: var(--ink-muted);
  text-transform: capitalize;
}

@media (max-width: 720px) {
  .who {
    display: none;
  }
}
</style>
