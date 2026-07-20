<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import CommentThread from '@/components/CommentThread.vue'
import TicketStatusBadge from '@/components/TicketStatusBadge.vue'
import AttachmentGallery from '@/components/AttachmentGallery.vue'
import { listStaffAgents } from '@/api/accounts'
import { createComment, escalateTicket, getTicket, updateTicket } from '@/api/tickets'
import { useAuthStore } from '@/stores/auth'
import type { StaffAgent, TicketDetail, TicketStatus } from '@/types'
import { MOVEMENT_LABELS, TICKET_STATUSES, displayName } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { user } = storeToRefs(auth)

const ticket = ref<TicketDetail | null>(null)
const agents = ref<StaffAgent[]>([])
const loading = ref(true)
const saving = ref(false)
const submitting = ref(false)
const escalating = ref(false)
const error = ref('')
const status = ref<TicketStatus>('open')

const escalateMode = ref<'next' | 'agent'>('next')
const escalateReason = ref('')
const targetAgentId = ref<number | ''>('')

const ticketId = computed(() => Number(route.params.id))

async function load() {
  loading.value = true
  error.value = ''
  try {
    ticket.value = await getTicket(ticketId.value)
    status.value = ticket.value.status
  } catch {
    error.value = 'Ticket not found or you do not have access.'
    ticket.value = null
  } finally {
    loading.value = false
  }
}

async function saveStatus() {
  if (!ticket.value) return
  saving.value = true
  error.value = ''
  try {
    ticket.value = await updateTicket(ticketId.value, { status: status.value })
  } catch {
    error.value = 'Could not update status.'
  } finally {
    saving.value = false
  }
}

async function assignToMe() {
  if (!user.value) return
  saving.value = true
  error.value = ''
  try {
    ticket.value = await updateTicket(ticketId.value, { assigned_agent: user.value.id })
  } catch {
    error.value = 'Could not assign ticket.'
  } finally {
    saving.value = false
  }
}

async function unassign() {
  saving.value = true
  error.value = ''
  try {
    ticket.value = await updateTicket(ticketId.value, { assigned_agent: null })
  } catch {
    error.value = 'Could not unassign ticket.'
  } finally {
    saving.value = false
  }
}

async function onEscalate() {
  const reason = escalateReason.value.trim()
  if (!reason) {
    error.value = 'Escalation reason is required.'
    return
  }
  if (escalateMode.value === 'agent' && !targetAgentId.value) {
    error.value = 'Select a target agent.'
    return
  }
  escalating.value = true
  error.value = ''
  try {
    ticket.value = await escalateTicket(ticketId.value, {
      mode: escalateMode.value,
      reason,
      target_agent_id: escalateMode.value === 'agent' ? Number(targetAgentId.value) : null,
    })
    escalateReason.value = ''
    targetAgentId.value = ''
    escalateMode.value = 'next'
  } catch (e: unknown) {
    const detail =
      e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null
    error.value = detail || 'Could not escalate ticket.'
  } finally {
    escalating.value = false
  }
}

async function onComment(payload: { body: string; isInternal: boolean; files: File[] }) {
  submitting.value = true
  error.value = ''
  try {
    await createComment(ticketId.value, payload.body, payload.isInternal, payload.files)
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

function personLabel(u: { first_name: string; last_name: string; username: string } | null) {
  return u ? displayName(u) : 'Unassigned'
}

function layerLabel(layer: { name: string; level: number } | null) {
  return layer ? `L${layer.level} ${layer.name}` : '—'
}

onMounted(async () => {
  try {
    agents.value = await listStaffAgents()
  } catch {
    /* escalate agent picker optional until load works */
  }
  await load()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <button type="button" class="btn btn-ghost" @click="router.push('/agent/queue')">
          ← Queue
        </button>
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
      <div class="card" style="margin-bottom: 1rem">
        <div class="panel actions">
          <div class="field" style="margin: 0; min-width: 180px">
            <label for="status">Status</label>
            <select id="status" v-model="status">
              <option v-for="s in TICKET_STATUSES" :key="s.value" :value="s.value">
                {{ s.label }}
              </option>
            </select>
          </div>
          <button class="btn" type="button" :disabled="saving" @click="saveStatus">
            {{ saving ? 'Saving…' : 'Update status' }}
          </button>
          <button
            class="btn btn-secondary"
            type="button"
            :disabled="saving || ticket.assigned_agent === user?.id"
            @click="assignToMe"
          >
            Assign to me
          </button>
          <button
            v-if="ticket.assigned_agent"
            class="btn btn-ghost"
            type="button"
            :disabled="saving"
            @click="unassign"
          >
            Unassign
          </button>
          <span class="muted assign-hint">
            Layer: {{ layerLabel(ticket.support_layer) }} · Agent #
            {{ ticket.assigned_agent ?? 'none' }}
          </span>
        </div>
      </div>

      <div class="card" style="margin-bottom: 1rem">
        <div class="panel">
          <h2>Escalate</h2>
          <p class="muted" style="margin-bottom: 0.75rem">
            Move this ticket to the next support layer or a specific agent. A reason is required and
            is recorded in movement history.
          </p>
          <div class="field">
            <label>Mode</label>
            <div class="row">
              <label class="check">
                <input v-model="escalateMode" type="radio" value="next" />
                Next support layer
              </label>
              <label class="check">
                <input v-model="escalateMode" type="radio" value="agent" />
                Specific agent
              </label>
            </div>
          </div>
          <div v-if="escalateMode === 'agent'" class="field">
            <label for="target-agent">Target agent</label>
            <select id="target-agent" v-model="targetAgentId" required>
              <option value="">Select agent</option>
              <option v-for="a in agents" :key="a.id" :value="a.id">
                {{ displayName(a) }}
                <template v-if="a.support_layers?.length">
                  ({{ a.support_layers.map((l) => `L${l.level}`).join(', ') }})
                </template>
              </option>
            </select>
          </div>
          <div class="field">
            <label for="escalate-reason">Reason</label>
            <textarea
              id="escalate-reason"
              v-model="escalateReason"
              rows="3"
              required
              placeholder="Why is this being escalated?"
            />
          </div>
          <button class="btn" type="button" :disabled="escalating" @click="onEscalate">
            {{ escalating ? 'Escalating…' : 'Escalate ticket' }}
          </button>
        </div>
      </div>

      <div class="card stack" style="gap: 0">
        <dl class="meta-grid">
          <div>
            <dt>Company</dt>
            <dd>{{ ticket.company.name }}</dd>
          </div>
          <div>
            <dt>Requester</dt>
            <dd>{{ displayName(ticket.requester) }}</dd>
          </div>
          <div>
            <dt>Support layer</dt>
            <dd>{{ layerLabel(ticket.support_layer) }}</dd>
          </div>
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
            <dt>First response due</dt>
            <dd>{{ formatDate(ticket.first_response_due_at) }}</dd>
          </div>
          <div>
            <dt>Resolution due</dt>
            <dd>{{ formatDate(ticket.resolution_due_at) }}</dd>
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
            allow-internal
            :submitting="submitting"
            @submit="onComment"
          />
        </div>

        <div class="panel">
          <h2>Movement history</h2>
          <div v-if="!ticket.movements?.length" class="muted">No assignment or escalation moves yet.</div>
          <ul v-else class="activity">
            <li v-for="m in ticket.movements" :key="m.id">
              <strong>{{ MOVEMENT_LABELS[m.movement_type] || m.movement_type }}</strong>
              <span>
                {{ personLabel(m.from_agent) }} → {{ personLabel(m.to_agent) }}
              </span>
              <span class="muted">
                {{ layerLabel(m.from_layer) }} → {{ layerLabel(m.to_layer) }}
              </span>
              <span class="muted">{{ formatDate(m.created_at) }}</span>
              <span v-if="m.actor" class="muted">by {{ displayName(m.actor) }}</span>
              <p v-if="m.reason" class="reason">{{ m.reason }}</p>
            </li>
          </ul>
        </div>

        <div v-if="ticket.activity_log?.length" class="panel">
          <h2>Status activity</h2>
          <ul class="activity">
            <li v-for="a in ticket.activity_log" :key="a.id">
              <span class="ticket-id">{{ a.status_from || '—' }} → {{ a.status_to }}</span>
              <span class="muted">{{ formatDate(a.created_at) }}</span>
              <span v-if="a.actor">{{ displayName(a.actor) }}</span>
              <span v-if="a.note">{{ a.note }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-end;
}

.assign-hint {
  margin-left: auto;
  font-size: 0.85rem;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
  color: var(--ink-muted);
}

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

.activity {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.activity li {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.85rem;
  font-size: 0.9rem;
  padding: 0.65rem 0;
  border-bottom: 1px solid var(--border);
  align-items: baseline;
}

.activity li:last-child {
  border-bottom: none;
}

.reason {
  flex-basis: 100%;
  margin: 0.15rem 0 0;
  color: var(--ink);
  white-space: pre-wrap;
}
</style>
