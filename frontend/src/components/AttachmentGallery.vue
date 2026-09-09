<script setup lang="ts">
import { getAccessToken } from '@/api/client'
import type { TicketAttachment } from '@/types'

defineProps<{
  attachments: TicketAttachment[]
}>()

function path(a: TicketAttachment) {
  return a.download_url || a.url || a.file
}

function preview(a: TicketAttachment) {
  return a.url || a.download_url || a.file
}

function isImage(a: TicketAttachment) {
  const name = (a.name || a.file || '').toLowerCase()
  return /\.(jpe?g|png|gif|webp)$/.test(name)
}

async function download(a: TicketAttachment, event: Event) {
  event.preventDefault()
  const url = path(a)
  if (!url) return
  try {
    const token = getAccessToken()
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('download failed')
    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = a.name || `attachment-${a.id}`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(objectUrl)
  } catch {
    window.open(url, '_blank', 'noopener')
  }
}
</script>

<template>
  <div v-if="attachments?.length" class="gallery">
    <a
      v-for="a in attachments"
      :key="a.id"
      class="shot"
      :href="path(a)"
      @click="download(a, $event)"
    >
      <img v-if="isImage(a)" :src="preview(a)" :alt="a.name || 'Attachment'" />
      <span v-else class="file-label">{{ a.name || `File #${a.id}` }}</span>
      <span class="dl">Download</span>
    </a>
  </div>
</template>

<style scoped>
.gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.65rem;
}
.shot {
  display: flex;
  flex-direction: column;
  width: 110px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
  text-decoration: none;
  color: inherit;
  background: #fff;
  cursor: pointer;
}
.shot img {
  width: 100%;
  height: 88px;
  object-fit: cover;
}
.file-label {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88px;
  padding: 0.35rem;
  font-size: 0.72rem;
  text-align: center;
  word-break: break-word;
}
.dl {
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
  padding: 0.25rem;
  background: #f4f7fa;
}
</style>
