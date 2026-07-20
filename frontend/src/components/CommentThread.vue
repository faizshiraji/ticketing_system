<script setup lang="ts">
import { ref } from 'vue'
import ImageAttachField from '@/components/ImageAttachField.vue'
import AttachmentGallery from '@/components/AttachmentGallery.vue'
import type { TicketComment } from '@/types'
import { displayName } from '@/types'

const props = defineProps<{
  comments: TicketComment[]
  allowInternal?: boolean
  submitting?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: { body: string; isInternal: boolean; files: File[] }]
}>()

const body = ref('')
const isInternal = ref(false)
const files = ref<File[]>([])

function onSubmit() {
  const text = body.value.trim()
  if (!text && !files.value.length) return
  if (!text) return
  emit('submit', {
    body: text,
    isInternal: props.allowInternal ? isInternal.value : false,
    files: [...files.value],
  })
  body.value = ''
  isInternal.value = false
  files.value = []
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <div class="thread">
    <div v-if="!comments.length" class="empty">No comments yet.</div>
    <article
      v-for="comment in comments"
      :key="comment.id"
      class="comment"
      :class="{ internal: comment.is_internal }"
    >
      <header>
        <strong>{{ displayName(comment.author) }}</strong>
        <span class="muted">{{ formatDate(comment.created_at) }}</span>
        <span v-if="comment.is_internal" class="note-tag">Internal</span>
      </header>
      <p>{{ comment.body }}</p>
      <AttachmentGallery :attachments="comment.attachments || []" />
    </article>

    <form class="composer" @submit.prevent="onSubmit">
      <div class="field">
        <label for="comment-body">{{ allowInternal && isInternal ? 'Internal note' : 'Reply' }}</label>
        <textarea id="comment-body" v-model="body" required rows="3" placeholder="Write a reply…" />
      </div>
      <ImageAttachField v-model="files" label="Attach images" />
      <div class="row">
        <label v-if="allowInternal" class="check">
          <input v-model="isInternal" type="checkbox" />
          Internal note (hidden from customer)
        </label>
        <button class="btn" type="submit" :disabled="submitting || !body.trim()">
          {{ submitting ? 'Sending…' : 'Send' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.thread {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.comment {
  padding: 0.9rem 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fbfcfd;
}

.comment.internal {
  background: var(--warn-soft);
  border-color: #fedf89;
}

.comment header {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
  align-items: baseline;
  margin-bottom: 0.35rem;
}

.comment p {
  margin: 0;
  color: var(--ink);
  white-space: pre-wrap;
}

.note-tag {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--warn);
}

.composer {
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.composer .row {
  justify-content: space-between;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.875rem;
  color: var(--ink-muted);
}

.empty {
  padding: 1rem 0;
  color: var(--ink-muted);
  font-size: 0.9rem;
}
</style>
