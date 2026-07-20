<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { createUser, deleteUser, listCompanies, listUsers, updateUser } from '@/api/accounts'
import { useAuthStore } from '@/stores/auth'
import type { AdminUser, Company, UserRole } from '@/types'
import { USER_ROLES, displayName } from '@/types'

const auth = useAuthStore()
const { isAdmin } = storeToRefs(auth)

const users = ref<AdminUser[]>([])
const companies = ref<Company[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const editingId = ref<number | null>(null)

const form = reactive({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  role: 'customer' as UserRole,
  company_id: '' as number | '',
  phone: '',
  is_active: true,
  password: '',
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [u, c] = await Promise.all([listUsers(), listCompanies()])
    users.value = u
    companies.value = c
  } catch {
    error.value = 'Could not load users.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editingId.value = null
  form.username = ''
  form.email = ''
  form.first_name = ''
  form.last_name = ''
  form.role = 'customer'
  form.company_id = companies.value[0]?.id ?? ''
  form.phone = ''
  form.is_active = true
  form.password = ''
}

function startEdit(u: AdminUser) {
  editingId.value = u.id
  form.username = u.username
  form.email = u.email
  form.first_name = u.first_name
  form.last_name = u.last_name
  form.role = u.role
  form.company_id = u.company?.id ?? ''
  form.phone = u.phone
  form.is_active = u.is_active
  form.password = ''
}

async function save() {
  if (!isAdmin.value) return
  saving.value = true
  error.value = ''
  try {
    const body = {
      username: form.username.trim(),
      email: form.email.trim(),
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      role: form.role,
      company_id:
        form.role === 'customer' ? Number(form.company_id) || null : form.company_id || null,
      phone: form.phone.trim(),
      is_active: form.is_active,
    }
    if (editingId.value) {
      await updateUser(editingId.value, {
        ...body,
        ...(form.password ? { password: form.password } : {}),
      })
    } else {
      if (!form.password) {
        error.value = 'Password is required for new users.'
        return
      }
      await createUser({ ...body, password: form.password })
    }
    startCreate()
    await load()
  } catch {
    error.value = 'Could not save user. Check required fields and company for customers.'
  } finally {
    saving.value = false
  }
}

async function remove(u: AdminUser) {
  if (!isAdmin.value) return
  if (!confirm(`Delete user ${u.username}?`)) return
  try {
    await deleteUser(u.id)
    if (editingId.value === u.id) startCreate()
    await load()
  } catch {
    error.value = 'Could not delete user.'
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
        <h1>Users</h1>
        <p>
          {{
            isAdmin
              ? 'Create and manage customer and staff accounts.'
              : 'Browse accounts. Only admins can create or edit users.'
          }}
        </p>
      </div>
      <RouterLink class="btn btn-secondary" to="/admin">Back to admin</RouterLink>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="layout">
      <form v-if="isAdmin" class="card panel" @submit.prevent="save">
        <h2>{{ editingId ? `Edit #${editingId}` : 'New user' }}</h2>
        <div class="field">
          <label for="username">Username</label>
          <input id="username" v-model="form.username" required />
        </div>
        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="form.email" type="email" />
        </div>
        <div class="row">
          <div class="field" style="flex: 1">
            <label for="first">First name</label>
            <input id="first" v-model="form.first_name" />
          </div>
          <div class="field" style="flex: 1">
            <label for="last">Last name</label>
            <input id="last" v-model="form.last_name" />
          </div>
        </div>
        <div class="field">
          <label for="role">Role</label>
          <select id="role" v-model="form.role">
            <option v-for="r in USER_ROLES" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </div>
        <div class="field">
          <label for="company">Company</label>
          <select id="company" v-model="form.company_id">
            <option value="">None (staff)</option>
            <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="field">
          <label for="phone">Phone</label>
          <input id="phone" v-model="form.phone" />
        </div>
        <div class="field">
          <label for="password">Password {{ editingId ? '(leave blank to keep)' : '' }}</label>
          <input id="password" v-model="form.password" type="password" :required="!editingId" />
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
              <th>User</th>
              <th>Role</th>
              <th>Company</th>
              <th>Active</th>
              <th v-if="isAdmin"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>
                <strong>{{ displayName(u) }}</strong>
                <div class="muted">{{ u.username }} · {{ u.email }}</div>
              </td>
              <td style="text-transform: capitalize">{{ u.role }}</td>
              <td>{{ u.company?.short_code || '—' }}</td>
              <td>{{ u.is_active ? 'Yes' : 'No' }}</td>
              <td v-if="isAdmin" class="row">
                <button class="btn btn-ghost" type="button" @click="startEdit(u)">Edit</button>
                <button class="btn btn-ghost" type="button" @click="remove(u)">Delete</button>
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
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
