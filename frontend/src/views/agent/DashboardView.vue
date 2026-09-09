<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchDashboardSummary } from '@/api/analytics'
import type { DashboardSummary } from '@/types'

const summary = ref<DashboardSummary | null>(null)
const loading = ref(true)
const error = ref('')

const dateFrom = ref('')
const dateTo = ref('')

const STATUS_CARDS = [
  { key: 'open', label: 'Open' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'resolved', label: 'Resolved' },
  { key: 'closed', label: 'Closed' },
  { key: 'reopened', label: 'Reopened' },
] as const

function defaultRange() {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - 30)
  dateTo.value = to.toISOString().slice(0, 10)
  dateFrom.value = from.toISOString().slice(0, 10)
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

function cardCount(key: string) {
  return summary.value?.status_summary?.[key] ?? summary.value?.by_status?.[key] ?? 0
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    summary.value = await fetchDashboardSummary({
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
    })
  } catch {
    error.value = 'Could not load dashboard summary.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  defaultRange()
  load()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p>Status summary, SLA breaches, and workload for the selected date range.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/agent/queue">Back to queue</RouterLink>
    </div>

    <div class="filters card">
      <div class="field">
        <label for="date-from">From date</label>
        <input id="date-from" v-model="dateFrom" type="date" />
      </div>
      <div class="field">
        <label for="date-to">To date</label>
        <input id="date-to" v-model="dateTo" type="date" />
      </div>
      <button class="btn" type="button" @click="load">Apply</button>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="card empty">Loading dashboard…</div>

    <template v-else-if="summary">
      <p class="muted" style="margin-bottom: 1rem">
        Generated {{ new Date(summary.generated_at).toLocaleString() }}
        <template v-if="summary.date_from && summary.date_to">
          · {{ summary.date_from }} → {{ summary.date_to }}
        </template>
      </p>

      <div class="stat-grid" style="margin-bottom: 1rem">
        <div v-for="card in STATUS_CARDS" :key="card.key" class="card stat">
          <div class="value">{{ cardCount(card.key) }}</div>
          <div class="label">{{ card.label }}</div>
        </div>
      </div>

      <div class="stat-grid" style="margin-bottom: 1rem">
        <div class="card stat">
          <div class="value">{{ summary.currently_open }}</div>
          <div class="label">Currently open (all active)</div>
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
          <h2>By category</h2>
          <ul class="list">
            <li v-for="row in summary.by_category" :key="row.category__name ?? 'none'">
              <span>{{ row.category__name || 'Uncategorized' }}</span>
              <strong>{{ row.count }}</strong>
            </li>
            <li v-if="!summary.by_category.length" class="muted">No data</li>
          </ul>
        </div>

        <div class="card panel">
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

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-end;
  padding: 1rem;
  margin-bottom: 1rem;
}

.filters .field {
  margin: 0;
  min-width: 160px;
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
