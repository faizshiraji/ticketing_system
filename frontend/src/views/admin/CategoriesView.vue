<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  createCategory,
  deleteCategory,
  listCategories,
  unwrapList,
  updateCategory,
} from '@/api/tickets'
import type { Category } from '@/types'

const categories = ref<Category[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const editingId = ref<number | null>(null)
const form = reactive({ name: '', is_active: true })

async function load() {
  loading.value = true
  error.value = ''
  try {
    categories.value = unwrapList(await listCategories())
  } catch {
    error.value = 'Could not load categories.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editingId.value = null
  form.name = ''
  form.is_active = true
}

function startEdit(c: Category) {
  editingId.value = c.id
  form.name = c.name
  form.is_active = c.is_active
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { name: form.name.trim(), is_active: form.is_active }
    if (editingId.value) await updateCategory(editingId.value, payload)
    else await createCategory(payload)
    startCreate()
    await load()
  } catch {
    error.value = 'Could not save category.'
  } finally {
    saving.value = false
  }
}

async function remove(c: Category) {
  if (!confirm(`Delete category ${c.name}?`)) return
  try {
    await deleteCategory(c.id)
    if (editingId.value === c.id) startCreate()
    await load()
  } catch {
    error.value = 'Could not delete category (it may be in use).'
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Categories</h1>
        <p>ERP and mobile-app support categories.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/admin">Back to admin</RouterLink>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="layout">
      <form class="card panel" @submit.prevent="save">
        <h2>{{ editingId ? `Edit #${editingId}` : 'New category' }}</h2>
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" required />
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
              <th>Active</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in categories" :key="c.id">
              <td>{{ c.name }}</td>
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
