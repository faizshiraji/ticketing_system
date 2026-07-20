<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { listStaffAgents } from '@/api/accounts'
import {
  createSupportLayer,
  deleteSupportLayer,
  listSupportLayers,
  updateSupportLayer,
} from '@/api/tickets'
import type { StaffAgent, SupportLayer } from '@/types'
import { displayName } from '@/types'

const layers = ref<SupportLayer[]>([])
const agents = ref<StaffAgent[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const editingId = ref<number | null>(null)
const form = reactive({
  name: '',
  level: 1,
  description: '',
  is_active: true,
  agent_ids: [] as number[],
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [layerList, agentList] = await Promise.all([listSupportLayers(), listStaffAgents()])
    layers.value = layerList
    agents.value = agentList
  } catch {
    error.value = 'Could not load support layers.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editingId.value = null
  form.name = ''
  form.level = (layers.value.at(-1)?.level ?? 0) + 1
  form.description = ''
  form.is_active = true
  form.agent_ids = []
}

function startEdit(layer: SupportLayer) {
  editingId.value = layer.id
  form.name = layer.name
  form.level = layer.level
  form.description = layer.description
  form.is_active = layer.is_active
  form.agent_ids = layer.agents.map((a) => a.id)
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = {
      name: form.name.trim(),
      level: Number(form.level),
      description: form.description.trim(),
      is_active: form.is_active,
      agent_ids: [...form.agent_ids],
    }
    if (editingId.value) await updateSupportLayer(editingId.value, payload)
    else await createSupportLayer(payload)
    startCreate()
    await load()
  } catch {
    error.value = 'Could not save support layer. Level and name must be unique.'
  } finally {
    saving.value = false
  }
}

async function remove(layer: SupportLayer) {
  if (!confirm(`Delete ${layer.name}? Tickets on this layer may block deletion.`)) return
  try {
    await deleteSupportLayer(layer.id)
    if (editingId.value === layer.id) startCreate()
    await load()
  } catch {
    error.value = 'Could not delete layer (it may still have tickets).'
  }
}

onMounted(async () => {
  await load()
  startCreate()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Support layers</h1>
        <p>Configure escalation tiers and assign agents to each layer.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/admin">Back to admin</RouterLink>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="layout">
      <form class="card panel" @submit.prevent="save">
        <h2>{{ editingId ? `Edit #${editingId}` : 'New layer' }}</h2>
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" required placeholder="e.g. Frontline" />
        </div>
        <div class="field">
          <label for="level">Level (lower = first line)</label>
          <input id="level" v-model.number="form.level" type="number" min="1" required />
        </div>
        <div class="field">
          <label for="description">Description</label>
          <textarea id="description" v-model="form.description" rows="3" />
        </div>
        <label class="check">
          <input v-model="form.is_active" type="checkbox" />
          Active
        </label>
        <div class="field" style="margin-top: 1rem">
          <label>Agents on this layer</label>
          <div class="agent-list">
            <label v-for="a in agents" :key="a.id" class="check">
              <input v-model="form.agent_ids" type="checkbox" :value="a.id" />
              {{ displayName(a) }}
              <span class="muted">({{ a.role }})</span>
            </label>
          </div>
        </div>
        <div class="row" style="margin-top: 1rem">
          <button class="btn" type="submit" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
          <button v-if="editingId" class="btn btn-ghost" type="button" @click="startCreate">
            Cancel
          </button>
        </div>
      </form>

      <div class="card table-wrap">
        <div v-if="loading" class="empty">Loading…</div>
        <table v-else class="data">
          <thead>
            <tr>
              <th>Level</th>
              <th>Name</th>
              <th>Agents</th>
              <th>Active</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="layer in layers" :key="layer.id">
              <td class="ticket-id">L{{ layer.level }}</td>
              <td>
                <strong>{{ layer.name }}</strong>
                <div v-if="layer.description" class="muted">{{ layer.description }}</div>
              </td>
              <td>
                <span v-if="!layer.agents.length" class="muted">None</span>
                <span v-else>{{ layer.agents.map((a) => displayName(a)).join(', ') }}</span>
              </td>
              <td>{{ layer.is_active ? 'Yes' : 'No' }}</td>
              <td class="row">
                <button class="btn btn-ghost" type="button" @click="startEdit(layer)">Edit</button>
                <button class="btn btn-ghost" type="button" @click="remove(layer)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(280px, 360px) 1fr;
  gap: 1rem;
}
h2 {
  font-size: 1rem;
  margin-bottom: 1rem;
}
.check {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
}
.agent-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  max-height: 220px;
  overflow: auto;
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: 8px;
}
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
