<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CommentThread from '@/components/CommentThread.vue'
import AttachmentGallery from '@/components/AttachmentGallery.vue'
import ImageAttachField from '@/components/ImageAttachField.vue'
import TicketStatusBadge from '@/components/TicketStatusBadge.vue'
import {
  createComment,
  getTicket,
  listCategories,
  listPriorities,
  unwrapList,
  updateTicket,
  uploadTicketAttachment,
} from '@/api/tickets'
import type { Category, Priority, TicketDetail } from '@/types'
import { displayName } from '@/types'

const route = useRoute()
const router = useRouter()
const ticket = ref<TicketDetail | null>(null)
const categories = ref<Category[]>([])
const priorities = ref<Priority[]>([])
const loading = ref(true)
const submitting = ref(false)
const saving = ref(false)
const error = ref('')
const editing = ref(false)

const editSubject = ref('')
const editDescription = ref('')
const editCategory = ref<number | ''>('')
const editPriority = ref<number | ''>('')
const editFiles = ref<File[]>([])

const ticketId = computed(() => Number(route.params.id))
const canEdit = computed(() => ticket.value?.status === 'open')

async function load() {
  loading.value = true
  error.value = ''
  try {
    ticket.value = await getTicket(ticketId.value)
    syncEditForm()
  } catch {
    error.value = 'Ticket not found or you do not have access.'
    ticket.value = null
  } finally {
    loading.value = false
  }
}

function syncEditForm() {
  if (!ticket.value) return
  editSubject.value = ticket.value.subject
  editDescription.value = ticket.value.description
  editCategory.value = ticket.value.category.id
  editPriority.value = ticket.value.priority.id
  editFiles.value = []
  editing.value = false
}

async function saveEdits() {
  if (!ticket.value || !canEdit.value) return
  saving.value = true
  error.value = ''
  try {
    ticket.value = await updateTicket(ticketId.value, {
      subject: editSubject.value.trim(),
      description: editDescription.value.trim(),
      category: Number(editCategory.value),
      priority: Number(editPriority.value),
    })
    for (const file of editFiles.value) {
      await uploadTicketAttachment(ticketId.value, file)
    }
    await load()
  } catch {
    error.value = 'Could not update ticket (only open tickets can be edited).'
  } finally {
    saving.value = false
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
  return new Date(iso).toLocaleDateString('en-GB', { timeZone: 'Asia/Dhaka' })
}

function formatTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('en-GB', { timeZone: 'Asia/Dhaka' })
}

function formatDateTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', { timeZone: 'Asia/Dhaka' })
}

onMounted(async () => {
  try {
    categories.value = unwrapList(await listCategories())
    priorities.value = unwrapList(await listPriorities())
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
            <dd>{{ formatDateTime(ticket.created_at) }}</dd>
          </div>
          <div>
            <dt>Resolution due</dt>
            <dd>{{ formatDateTime(ticket.resolution_due_at) }}</dd>
          </div>
          <div>
            <dt>Resolution date</dt>
            <dd>{{ formatDate(ticket.resolved_at) }}</dd>
          </div>
          <div>
            <dt>Resolution time</dt>
            <dd>{{ formatTime(ticket.resolved_at) }}</dd>
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
          <div class="panel-head">
            <h2>Description</h2>
            <button
              v-if="canEdit && !editing"
              type="button"
              class="btn btn-secondary"
              @click="editing = true"
            >
              Edit ticket
            </button>
          </div>

          <template v-if="editing && canEdit">
            <div class="field">
              <label for="subject">Subject</label>
              <input id="subject" v-model="editSubject" required />
            </div>
            <div class="field">
              <label for="category">Category</label>
              <select id="category" v-model="editCategory" required>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="field">
              <label for="priority">Priority</label>
              <select id="priority" v-model="editPriority" required>
                <option v-for="p in priorities" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="field">
              <label for="description">Description</label>
              <textarea id="description" v-model="editDescription" rows="5" required />
            </div>
            <ImageAttachField v-model="editFiles" label="Add attachments" />
            <div class="row">
              <button class="btn" type="button" :disabled="saving" @click="saveEdits">
                {{ saving ? 'Saving…' : 'Save changes' }}
              </button>
              <button class="btn btn-ghost" type="button" @click="syncEditForm">Cancel</button>
            </div>
          </template>
          <template v-else>
            <p class="body">{{ ticket.description }}</p>
            <AttachmentGallery :attachments="ticket.attachments || []" />
            <p v-if="!canEdit" class="muted hint">
              This ticket has been received by support and can no longer be edited.
            </p>
          </template>
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

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.panel-head h2 {
  margin: 0;
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

.hint {
  margin-top: 0.75rem;
  font-size: 0.85rem;
}
</style>
