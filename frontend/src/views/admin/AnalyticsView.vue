<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listCompanies } from '@/api/accounts'
import { fetchReports } from '@/api/analytics'
import type { AnalyticsReport, Company, DayCount } from '@/types'

const router = useRouter()
const report = ref<AnalyticsReport | null>(null)
const companies = ref<Company[]>([])
const loading = ref(true)
const error = ref('')
const companyId = ref<number | ''>('')
const days = ref(30)

const maxCreated = computed(() =>
  Math.max(1, ...(report.value?.tickets_created_by_day.map((d) => d.count) ?? [1])),
)
const maxResolved = computed(() =>
  Math.max(1, ...(report.value?.tickets_resolved_by_day.map((d) => d.count) ?? [1])),
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    report.value = await fetchReports({
      company: companyId.value || undefined,
      days: days.value,
    })
  } catch {
    error.value = 'Could not load analytics report.'
    report.value = null
  } finally {
    loading.value = false
  }
}

function barHeight(row: DayCount, max: number) {
  return `${Math.max(4, (row.count / max) * 100)}%`
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function openTicket(id: number) {
  router.push({ name: 'agent-ticket-detail', params: { id } })
}

onMounted(async () => {
  try {
    companies.value = await listCompanies()
  } catch {
    /* optional */
  }
  await load()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Analytics reports</h1>
        <p>Trends, period totals, and open SLA breaches.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/admin">Back to admin</RouterLink>
    </div>

    <div class="filters card">
      <div class="field">
        <label for="company">Company</label>
        <select id="company" v-model="companyId">
          <option value="">All companies</option>
          <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="field">
        <label for="days">Days</label>
        <select id="days" v-model.number="days">
          <option :value="7">7</option>
          <option :value="14">14</option>
          <option :value="30">30</option>
          <option :value="90">90</option>
        </select>
      </div>
      <button class="btn" type="button" @click="load">Apply</button>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="card empty">Loading report…</div>

    <template v-else-if="report">
      <p class="muted" style="margin-bottom: 1rem">
        Generated {{ formatDate(report.generated_at) }} · last {{ report.days }} days
      </p>

      <div class="stat-grid" style="margin-bottom: 1rem">
        <div class="card stat">
          <div class="value">{{ report.created_in_period }}</div>
          <div class="label">Created in period</div>
        </div>
        <div class="card stat">
          <div class="value">{{ report.resolved_in_period }}</div>
          <div class="label">Resolved in period</div>
        </div>
        <div class="card stat">
          <div class="value" :class="{ danger: report.open_sla_breached.length > 0 }">
            {{ report.open_sla_breached.length }}
          </div>
          <div class="label">Open SLA breached</div>
        </div>
      </div>

      <div class="charts">
        <div class="card panel">
          <h2>Tickets created</h2>
          <div class="bars">
            <div
              v-for="row in report.tickets_created_by_day"
              :key="'c-' + row.date"
              class="bar-col"
              :title="`${row.date}: ${row.count}`"
            >
              <div class="bar" :style="{ height: barHeight(row, maxCreated) }" />
            </div>
          </div>
        </div>
        <div class="card panel">
          <h2>Tickets resolved</h2>
          <div class="bars">
            <div
              v-for="row in report.tickets_resolved_by_day"
              :key="'r-' + row.date"
              class="bar-col"
              :title="`${row.date}: ${row.count}`"
            >
              <div class="bar resolved" :style="{ height: barHeight(row, maxResolved) }" />
            </div>
          </div>
        </div>
      </div>

      <div class="card table-wrap" style="margin-top: 1rem">
        <div class="panel" style="border-bottom: 1px solid var(--border)">
          <h2>Open SLA-breached tickets</h2>
        </div>
        <div v-if="!report.open_sla_breached.length" class="empty">No open breaches.</div>
        <table v-else class="data">
          <thead>
            <tr>
              <th>ID</th>
              <th>Subject</th>
              <th>Company</th>
              <th>Status</th>
              <th>Due</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in report.open_sla_breached"
              :key="t.id"
              @click="openTicket(t.id)"
            >
              <td class="ticket-id">#{{ t.id }}</td>
              <td>{{ t.subject }}</td>
              <td>{{ t.company.short_code }}</td>
              <td style="text-transform: capitalize">{{ t.status.replace('_', ' ') }}</td>
              <td class="muted">{{ formatDate(t.resolution_due_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
h2 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 140px;
  padding-top: 0.5rem;
}

.bar-col {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  align-items: flex-end;
}

.bar {
  width: 100%;
  background: var(--accent);
  border-radius: 3px 3px 0 0;
  opacity: 0.85;
}

.bar.resolved {
  background: var(--ok);
}

.danger {
  color: var(--danger);
}
</style>
