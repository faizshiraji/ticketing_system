<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  createCompany,
  deleteCompany,
  listCompanies,
  updateCompany,
} from '@/api/accounts'
import type { Company } from '@/types'

const companies = ref<Company[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const editingId = ref<number | null>(null)
const form = reactive({ name: '', short_code: '', is_active: true })

async function load() {
  loading.value = true
  error.value = ''
  try {
    companies.value = await listCompanies()
  } catch {
    error.value = 'Could not load companies.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editingId.value = null
  form.name = ''
  form.short_code = ''
  form.is_active = true
}

function startEdit(c: Company) {
  editingId.value = c.id
  form.name = c.name
  form.short_code = c.short_code
  form.is_active = c.is_active
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = {
      name: form.name.trim(),
      short_code: form.short_code.trim().toUpperCase(),
      is_active: form.is_active,
    }
    if (editingId.value) {
      await updateCompany(editingId.value, payload)
    } else {
      await createCompany(payload)
    }
    startCreate()
    await load()
  } catch {
    error.value = 'Could not save company.'
  } finally {
    saving.value = false
  }
}

async function remove(c: Company) {
  if (!confirm(`Delete company ${c.name}?`)) return
  error.value = ''
  try {
    await deleteCompany(c.id)
    if (editingId.value === c.id) startCreate()
    await load()
  } catch {
    error.value = 'Could not delete company (it may still have users or tickets).'
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Companies</h1>
        <p>Client companies that raise support tickets.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/admin">Back to admin</RouterLink>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="layout">
      <form class="card panel" @submit.prevent="save">
        <h2>{{ editingId ? `Edit #${editingId}` : 'New company' }}</h2>
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" required />
        </div>
        <div class="field">
          <label for="code">Short code</label>
          <input id="code" v-model="form.short_code" required maxlength="20" />
        </div>
        <label class="check">
          <input v-model="form.is_active" type="checkbox" />
          Active
        </label>
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
              <th>Code</th>
              <th>Active</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in companies" :key="c.id">
              <td>{{ c.name }}</td>
              <td class="ticket-id">{{ c.short_code }}</td>
              <td>{{ c.is_active ? 'Yes' : 'No' }}</td>
              <td class="row">
                <button class="btn btn-ghost" type="button" @click="startEdit(c)">Edit</button>
                <button class="btn btn-ghost" type="button" @click="remove(c)">Delete</button>
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

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
}

@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
