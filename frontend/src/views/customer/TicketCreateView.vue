<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ImageAttachField from '@/components/ImageAttachField.vue'
import {
  createTicket,
  listCategories,
  listPriorities,
  unwrapList,
  uploadTicketAttachment,
} from '@/api/tickets'
import type { Category, Priority } from '@/types'

const router = useRouter()
const categories = ref<Category[]>([])
const priorities = ref<Priority[]>([])
const subject = ref('')
const description = ref('')
const category = ref<number | ''>('')
const priority = ref<number | ''>('')
const images = ref<File[]>([])
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const [cats, pris] = await Promise.all([listCategories(), listPriorities()])
    categories.value = unwrapList(cats)
    priorities.value = unwrapList(pris)
    if (categories.value[0]) category.value = categories.value[0].id
    if (priorities.value[0]) priority.value = priorities.value[0].id
  } catch {
    error.value = 'Could not load categories or priorities.'
  }
})

async function onSubmit() {
  if (!category.value || !priority.value) return
  loading.value = true
  error.value = ''
  try {
    const ticket = await createTicket({
      subject: subject.value.trim(),
      description: description.value.trim(),
      category: category.value,
      priority: priority.value,
    })
    for (const file of images.value) {
      await uploadTicketAttachment(ticket.id, file)
    }
    await router.push({ name: 'customer-ticket-detail', params: { id: ticket.id } })
  } catch {
    error.value = 'Could not create ticket. Check the form and try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>New ticket</h1>
        <p>Describe the ERP or mobile-app issue so support can help.</p>
      </div>
      <RouterLink class="btn btn-secondary" to="/tickets">Back</RouterLink>
    </div>

    <form class="card panel" @submit.prevent="onSubmit">
      <div v-if="error" class="error-banner">{{ error }}</div>

      <div class="field">
        <label for="subject">Subject</label>
        <input id="subject" v-model="subject" required maxlength="200" />
      </div>

      <div class="field">
        <label for="description">Description</label>
        <textarea id="description" v-model="description" required rows="6" />
      </div>

      <ImageAttachField v-model="images" label="Screenshots / images" />

      <div class="row" style="align-items: stretch">
        <div class="field" style="flex: 1; min-width: 180px">
          <label for="category">Category</label>
          <select id="category" v-model="category" required>
            <option disabled value="">Select category</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="field" style="flex: 1; min-width: 180px">
          <label for="priority">Priority</label>
          <select id="priority" v-model="priority" required>
            <option disabled value="">Select priority</option>
            <option v-for="p in priorities" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
      </div>

      <button class="btn" type="submit" :disabled="loading">
        {{ loading ? 'Submitting…' : 'Submit ticket' }}
      </button>
    </form>
  </div>
</template>
