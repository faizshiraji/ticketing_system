<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listPublicCompanies } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { Company } from '@/types'

const username = ref('')
const password = ref('')
const company = ref('')
const companies = ref<Company[]>([])
const error = ref('')
const loading = ref(false)

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

onMounted(async () => {
  try {
    companies.value = await listPublicCompanies()
    const preferred = companies.value.find((c) => c.short_code.toLowerCase() === 'ccl')
    company.value = preferred?.short_code || companies.value[0]?.short_code || ''
  } catch {
    companies.value = []
  }
})

async function onSubmit() {
  error.value = ''
  if (!company.value) {
    error.value = 'Select a company.'
    return
  }
  loading.value = true
  try {
    const user = await auth.login(username.value.trim(), password.value, company.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : null
    if (redirect) {
      await router.replace(redirect)
      return
    }
    await router.replace(auth.homePathFor(user.role))
  } catch {
    error.value = 'Invalid credentials or company selection.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <form class="card login-card" @submit.prevent="onSubmit">
      <div class="brand">
        <span class="mark">{{ company ? company.toUpperCase() : 'CCL' }}</span>
        <div>
          <h1>Support Desk</h1>
          <p>Sign in to raise or manage ERP support tickets.</p>
        </div>
      </div>

      <div v-if="error" class="error-banner">{{ error }}</div>

      <div class="field">
        <label for="company">Company</label>
        <select id="company" v-model="company" required>
          <option disabled value="">Select company</option>
          <option v-for="c in companies" :key="c.id" :value="c.short_code">
            {{ c.name }} ({{ c.short_code.toUpperCase() }})
          </option>
        </select>
      </div>

      <div class="field">
        <label for="username">Username</label>
        <input id="username" v-model="username" autocomplete="username" required autofocus />
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
        />
      </div>

      <button class="btn" type="submit" :disabled="loading || !company">
        {{ loading ? 'Signing in…' : 'Sign in' }}
      </button>

      <p class="hint muted">
        Demo: company <code>CCL</code>, user <code>ccl.user</code> / <code>agent1</code> —
        password <code>Test@123</code>
      </p>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
}

.login-card {
  width: min(420px, 100%);
  padding: 1.75rem;
}

.brand {
  display: flex;
  gap: 0.9rem;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.brand h1 {
  font-size: 1.35rem;
}

.brand p {
  margin: 0;
  font-size: 0.9rem;
}

.mark {
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 10px;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 0.75rem;
}

.btn {
  width: 100%;
  margin-top: 0.25rem;
}

.hint {
  margin: 1.25rem 0 0;
  font-size: 0.8rem;
}

.hint code {
  font-family: var(--mono);
  font-size: 0.78rem;
  background: #eef2f6;
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
}
</style>
