<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CommentThread from '@/components/CommentThread.vue'
import AttachmentGallery from '@/components/AttachmentGallery.vue'
import TicketStatusBadge from '@/components/TicketStatusBadge.vue'
import { createComment, getTicket } from '@/api/tickets'
import type { TicketDetail } from '@/types'
import { displayName } from '@/types'

const route = useRoute()
const router = useRouter()
const ticket = ref<TicketDetail | null>(null)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

const ticketId = computed(() => Number(route.params.id))

async function load() {
  loading.value = true
  error.value = ''
  try {
    ticket.value = await getTicket(ticketId.value)
  } catch {
    error.value = 'Ticket not found or you do not have access.'
    ticket.value = null
  } finally {
    loading.value = false
  }
}

async function onComment(payload: { body: string; isInternal: boolean; files: File[] }) {
  submitting.value = true
  error.value = ''
  try {
    await createComment(ticketId.value, payload.body, false, payload.files)
    await load()
  } catch {
    error.value = 'Could not post comment.'
  } finally {
    submitting.value = false
  }
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <button type="button" class="btn btn-ghost" @click="router.push('/tickets')">← Back</button>
        <h1 v-if="ticket">#{{ ticket.id }} {{ ticket.subject }}</h1>
        <h1 v-else>Ticket</h1>
      </div>
      <TicketStatusBadge
        v-if="ticket"
        :status="ticket.status"
        :breached="ticket.is_sla_breached"
      />
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="card empty">Loading…</div>

    <template v-else-if="ticket">
      <div class="card stack" style="gap: 0">
        <dl class="meta-grid">
          <div>
            <dt>Category</dt>
            <dd>{{ ticket.category.name }}</dd>
          </div>
          <div>
            <dt>Priority</dt>
            <dd>{{ ticket.priority.name }}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{{ formatDate(ticket.created_at) }}</dd>
          </div>
          <div>
            <dt>Resolution due</dt>
            <dd>{{ formatDate(ticket.resolution_due_at) }}</dd>
          </div>
          <div>
            <dt>Requester</dt>
            <dd>{{ displayName(ticket.requester) }}</dd>
          </div>
          <div>
            <dt>Company</dt>
            <dd>{{ ticket.company.name }}</dd>
          </div>
        </dl>

        <div class="panel">
          <h2>Description</h2>
          <p class="body">{{ ticket.description }}</p>
          <AttachmentGallery :attachments="ticket.attachments || []" />
        </div>

        <div class="panel">
          <h2>Conversation</h2>
          <CommentThread
            :comments="ticket.comments"
            :submitting="submitting"
            @submit="onComment"
          />
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

.body {
  color: var(--ink);
  white-space: pre-wrap;
  margin: 0;
}

.btn-ghost {
  margin-bottom: 0.5rem;
  padding-left: 0;
}
</style>
