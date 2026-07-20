<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import TicketStatusBadge from '@/components/TicketStatusBadge.vue'
import TicketFilters from '@/components/TicketFilters.vue'
import { listCategories, listPriorities, listTickets, unwrapList } from '@/api/tickets'
import { useAuthStore } from '@/stores/auth'
import type { Category, Priority, TicketListItem, TicketStatus } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const { user } = storeToRefs(auth)

const tickets = ref<TicketListItem[]>([])
const categories = ref<Category[]>([])
const priorities = ref<Priority[]>([])
const loading = ref(true)
const error = ref('')
const status = ref<TicketStatus | ''>('')
const category = ref<number | ''>('')
const priority = ref<number | ''>('')
const assignedMine = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listTickets({
      status: status.value,
      category: category.value,
      priority: priority.value,
      assigned_agent: assignedMine.value && user.value ? user.value.id : '',
    })
    tickets.value = data.results
  } catch {
    error.value = 'Could not load ticket queue.'
  } finally {
    loading.value = false
  }
}

function reset() {
  status.value = ''
  category.value = ''
  priority.value = ''
  assignedMine.value = false
  load()
}

function openTicket(id: number) {
  router.push({ name: 'agent-ticket-detail', params: { id } })
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}

onMounted(async () => {
  try {
    const [cats, pris] = await Promise.all([listCategories(), listPriorities()])
    categories.value = unwrapList(cats)
    priorities.value = unwrapList(pris)
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
        <h1>Ticket queue</h1>
        <p>Triage and update support tickets across CCL and CCDL.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/agent/dashboard">Dashboard</RouterLink>
    </div>

    <TicketFilters
      v-model:status="status"
      v-model:category="category"
      v-model:priority="priority"
      v-model:assigned-mine="assignedMine"
      :categories="categories"
      :priorities="priorities"
      show-assigned-mine
      @apply="load"
      @reset="reset"
    />

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="card table-wrap">
      <div v-if="loading" class="empty">Loading queue…</div>
      <div v-else-if="!tickets.length" class="empty">No tickets match these filters.</div>
      <table v-else class="data">
        <thead>
          <tr>
            <th>ID</th>
            <th>Subject</th>
            <th>Company</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Due</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tickets" :key="t.id" @click="openTicket(t.id)">
            <td class="ticket-id">#{{ t.id }}</td>
            <td>{{ t.subject }}</td>
            <td>{{ t.company.short_code }}</td>
            <td>{{ t.category.name }}</td>
            <td>{{ t.priority.name }}</td>
            <td>
              <TicketStatusBadge :status="t.status" :breached="t.is_sla_breached" />
            </td>
            <td class="muted">
              {{ t.resolution_due_at ? formatDate(t.resolution_due_at) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
