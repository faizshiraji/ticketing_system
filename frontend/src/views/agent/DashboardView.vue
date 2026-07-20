<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchDashboardSummary } from '@/api/analytics'
import type { DashboardSummary } from '@/types'
import { TICKET_STATUSES } from '@/types'

const summary = ref<DashboardSummary | null>(null)
const loading = ref(true)
const error = ref('')

function statusLabel(key: string) {
  return TICKET_STATUSES.find((s) => s.value === key)?.label ?? key
}

function formatDuration(seconds: number | null) {
  if (seconds == null) return '—'
  const hours = seconds / 3600
  if (hours < 24) return `${hours.toFixed(1)} h`
  return `${(hours / 24).toFixed(1)} d`
}

function agentName(row: DashboardSummary['agent_workload'][number]) {
  const full = `${row.assigned_agent__first_name} ${row.assigned_agent__last_name}`.trim()
  return full || `Agent #${row.assigned_agent__id}`
}

onMounted(async () => {
  try {
    summary.value = await fetchDashboardSummary()
  } catch {
    error.value = 'Could not load dashboard summary.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p>Open workload, SLA breaches, and resolution trends.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/agent/queue">Back to queue</RouterLink>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="card empty">Loading dashboard…</div>

    <template v-else-if="summary">
      <p class="muted" style="margin-bottom: 1rem">
        Generated {{ new Date(summary.generated_at).toLocaleString() }}
      </p>

      <div class="stat-grid" style="margin-bottom: 1rem">
        <div class="card stat">
          <div class="value">{{ summary.currently_open }}</div>
          <div class="label">Currently open</div>
        </div>
        <div class="card stat">
          <div class="value" :class="{ danger: summary.currently_sla_breached > 0 }">
            {{ summary.currently_sla_breached }}
          </div>
          <div class="label">SLA breached</div>
        </div>
        <div class="card stat">
          <div class="value">{{ formatDuration(summary.avg_resolution_seconds) }}</div>
          <div class="label">Avg resolution</div>
        </div>
      </div>

      <div class="grid-2">
        <div class="card panel">
          <h2>By status</h2>
          <ul class="list">
            <li v-for="(count, status) in summary.by_status" :key="status">
              <span>{{ statusLabel(String(status)) }}</span>
              <strong>{{ count }}</strong>
            </li>
            <li v-if="!Object.keys(summary.by_status).length" class="muted">No data</li>
          </ul>
        </div>

        <div class="card panel">
          <h2>By category</h2>
          <ul class="list">
            <li v-for="row in summary.by_category" :key="row.category__name ?? 'none'">
              <span>{{ row.category__name || 'Uncategorized' }}</span>
              <strong>{{ row.count }}</strong>
            </li>
            <li v-if="!summary.by_category.length" class="muted">No data</li>
          </ul>
        </div>

        <div class="card panel" style="grid-column: 1 / -1">
          <h2>Agent workload (open)</h2>
          <ul class="list">
            <li v-for="row in summary.agent_workload" :key="row.assigned_agent__id">
              <span>{{ agentName(row) }}</span>
              <strong>{{ row.open_tickets }}</strong>
            </li>
            <li v-if="!summary.agent_workload.length" class="muted">No assigned open tickets</li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
h2 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.925rem;
}

.list li:last-child {
  border-bottom: none;
}

.danger {
  color: var(--danger);
}
</style>
