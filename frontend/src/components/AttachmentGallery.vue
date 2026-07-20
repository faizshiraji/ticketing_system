<script setup lang="ts">
import type { TicketAttachment } from '@/types'

defineProps<{
  attachments: TicketAttachment[]
}>()

function src(a: TicketAttachment) {
  return a.url || a.file
}
</script>

<template>
  <div v-if="attachments?.length" class="gallery">
    <a
      v-for="a in attachments"
      :key="a.id"
      class="shot"
      :href="src(a)"
      target="_blank"
      rel="noopener"
    >
      <img :src="src(a)" alt="Attachment" />
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
  display: block;
  width: 88px;
  height: 88px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
}
.shot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
