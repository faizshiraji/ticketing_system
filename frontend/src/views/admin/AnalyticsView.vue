<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listCompanies } from '@/api/accounts'
import { fetchReports } from '@/api/analytics'
import type { AnalyticsReport, Company, DayCount } from '@/types'
import { TICKET_STATUSES } from '@/types'

const router = useRouter()
const report = ref<AnalyticsReport | null>(null)
const companies = ref<Company[]>([])
const loading = ref(true)
const error = ref('')
const companyId = ref<number | ''>('')
const dateFrom = ref('')
const dateTo = ref('')

const maxCreated = computed(() =>
  Math.max(1, ...(report.value?.tickets_created_by_day.map((d) => d.count) ?? [1])),
)
const maxResolved = computed(() =>
  Math.max(1, ...(report.value?.tickets_resolved_by_day.map((d) => d.count) ?? [1])),
)

function defaultRange() {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - 30)
  dateTo.value = to.toISOString().slice(0, 10)
  dateFrom.value = from.toISOString().slice(0, 10)
}

function statusLabel(key: string) {
  return TICKET_STATUSES.find((s) => s.value === key)?.label ?? key
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    report.value = await fetchReports({
      company: companyId.value || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
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
  return new Date(iso).toLocaleString('en-GB', { timeZone: 'Asia/Dhaka' })
}

function openTicket(id: number) {
  router.push({ name: 'agent-ticket-detail', params: { id } })
}

onMounted(async () => {
  defaultRange()
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
        <p>Status-wise and category-wise summaries for the selected date range.</p>
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
    <div v-if="loading" class="card empty">Loading report…</div>

    <template v-else-if="report">
      <p class="muted" style="margin-bottom: 1rem">
        Generated {{ formatDate(report.generated_at) }}
        <template v-if="report.date_from && report.date_to">
          · {{ report.date_from }} → {{ report.date_to }}
        </template>
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

      <div class="grid-2" style="margin-bottom: 1rem">
        <div class="card panel">
          <h2>Status-wise summary</h2>
          <ul class="list">
            <li v-for="row in report.by_status || []" :key="row.status">
              <span>{{ statusLabel(row.status) }}</span>
              <strong>{{ row.count }}</strong>
            </li>
            <li v-if="!(report.by_status || []).length" class="muted">No data</li>
          </ul>
        </div>
        <div class="card panel">
          <h2>Category-wise summary</h2>
          <ul class="list">
            <li
              v-for="row in report.by_category || []"
              :key="String(row.category__id ?? row.category__name)"
            >
              <span>{{ row.category__name || 'Uncategorized' }}</span>
              <strong>{{ row.count }}</strong>
            </li>
            <li v-if="!(report.by_category || []).length" class="muted">No data</li>
          </ul>
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
          <h2>Ticket detail (period)</h2>
        </div>
        <div v-if="!(report.tickets || []).length" class="empty">No tickets in range.</div>
        <table v-else class="data">
          <thead>
            <tr>
              <th>ID</th>
              <th>Subject</th>
              <th>Status</th>
              <th>Category</th>
              <th>Created</th>
              <th>Resolved</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in report.tickets" :key="t.id" @click="openTicket(t.id)">
              <td class="ticket-id">#{{ t.id }}</td>
              <td>{{ t.subject }}</td>
              <td>{{ statusLabel(t.status) }}</td>
              <td>{{ t.category || '—' }}</td>
              <td class="muted">{{ formatDate(t.created_at) }}</td>
              <td class="muted">{{ formatDate(t.resolved_at) }}</td>
            </tr>
          </tbody>
        </table>
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
              <td>{{ statusLabel(t.status) }}</td>
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
  min-width: 140px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
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
