<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import TicketStatusBadge from '@/components/TicketStatusBadge.vue'
import TicketFilters from '@/components/TicketFilters.vue'
import { listCategories, listPriorities, listTickets, unwrapList } from '@/api/tickets'
import type { Category, Priority, TicketListItem, TicketStatus } from '@/types'

const router = useRouter()
const tickets = ref<TicketListItem[]>([])
const categories = ref<Category[]>([])
const priorities = ref<Priority[]>([])
const loading = ref(true)
const error = ref('')
const status = ref<TicketStatus | ''>('')
const category = ref<number | ''>('')
const priority = ref<number | ''>('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listTickets({
      status: status.value,
      category: category.value,
      priority: priority.value,
    })
    tickets.value = data.results
  } catch {
    error.value = 'Could not load tickets.'
  } finally {
    loading.value = false
  }
}

function reset() {
  status.value = ''
  category.value = ''
  priority.value = ''
  load()
}

function openTicket(id: number) {
  router.push({ name: 'customer-ticket-detail', params: { id } })
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
    /* filters optional */
  }
  await load()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>My tickets</h1>
        <p>Track ERP and mobile-app support requests for your company.</p>
      </div>
      <RouterLink class="btn" to="/tickets/new">New ticket</RouterLink>
    </div>

    <TicketFilters
      v-model:status="status"
      v-model:category="category"
      v-model:priority="priority"
      :categories="categories"
      :priorities="priorities"
      @apply="load"
      @reset="reset"
    />

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="card table-wrap">
      <div v-if="loading" class="empty">Loading tickets…</div>
      <div v-else-if="!tickets.length" class="empty">No tickets yet. Create one to get started.</div>
      <table v-else class="data">
        <thead>
          <tr>
            <th>ID</th>
            <th>Subject</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tickets" :key="t.id" @click="openTicket(t.id)">
            <td class="ticket-id">#{{ t.id }}</td>
            <td>{{ t.subject }}</td>
            <td>{{ t.category.name }}</td>
            <td>{{ t.priority.name }}</td>
            <td>
              <TicketStatusBadge :status="t.status" :breached="t.is_sla_breached" />
            </td>
            <td class="muted">{{ formatDate(t.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
