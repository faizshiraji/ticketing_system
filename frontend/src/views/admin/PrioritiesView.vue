<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  createPriority,
  deletePriority,
  listPriorities,
  unwrapList,
  updatePriority,
} from '@/api/tickets'
import type { Priority } from '@/types'

const priorities = ref<Priority[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const editingId = ref<number | null>(null)
const form = reactive({ name: '', rank: 1 })

async function load() {
  loading.value = true
  error.value = ''
  try {
    priorities.value = unwrapList(await listPriorities())
  } catch {
    error.value = 'Could not load priorities.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editingId.value = null
  form.name = ''
  form.rank = (priorities.value.at(-1)?.rank ?? 0) + 1
}

function startEdit(p: Priority) {
  editingId.value = p.id
  form.name = p.name
  form.rank = p.rank
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { name: form.name.trim(), rank: Number(form.rank) }
    if (editingId.value) await updatePriority(editingId.value, payload)
    else await createPriority(payload)
    startCreate()
    await load()
  } catch {
    error.value = 'Could not save priority.'
  } finally {
    saving.value = false
  }
}

async function remove(p: Priority) {
  if (!confirm(`Delete priority ${p.name}?`)) return
  try {
    await deletePriority(p.id)
    if (editingId.value === p.id) startCreate()
    await load()
  } catch {
    error.value = 'Could not delete priority (it may be in use).'
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
        <h1>Priorities</h1>
        <p>Lower rank means higher urgency.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/admin">Back to admin</RouterLink>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="layout">
      <form class="card panel" @submit.prevent="save">
        <h2>{{ editingId ? `Edit #${editingId}` : 'New priority' }}</h2>
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" required />
        </div>
        <div class="field">
          <label for="rank">Rank</label>
          <input id="rank" v-model.number="form.rank" type="number" min="1" required />
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
              <th>Name</th>
              <th>Rank</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in priorities" :key="p.id">
              <td>{{ p.name }}</td>
              <td class="ticket-id">{{ p.rank }}</td>
              <td class="row">
                <button class="btn btn-ghost" type="button" @click="startEdit(p)">Edit</button>
                <button class="btn btn-ghost" type="button" @click="remove(p)">Delete</button>
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
  grid-template-columns: minmax(260px, 320px) 1fr;
  gap: 1rem;
}
h2 {
  font-size: 1rem;
  margin-bottom: 1rem;
}
@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
