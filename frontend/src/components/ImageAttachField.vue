<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const ALLOWED_EXT = /\.(jpe?g|png|gif|webp|pdf|xlsx?)$/i
const MAX_BYTES = 10 * 1024 * 1024

const props = withDefaults(
  defineProps<{
    modelValue?: File[]
    maxFiles?: number
    label?: string
  }>(),
  {
    modelValue: () => [],
    maxFiles: 5,
    label: 'Attachments',
  },
)

const emit = defineEmits<{
  'update:modelValue': [files: File[]]
}>()

const error = ref('')
const inputKey = ref(0)

const files = computed({
  get: () => props.modelValue,
  set: (value: File[]) => emit('update:modelValue', value),
})

const previews = ref<{ name: string; url: string; isImage: boolean }[]>([])

watch(
  () => props.modelValue,
  (list) => {
    for (const p of previews.value) {
      if (p.isImage) URL.revokeObjectURL(p.url)
    }
    previews.value = list.map((f) => {
      const isImage = f.type.startsWith('image/')
      return { name: f.name, url: isImage ? URL.createObjectURL(f) : '', isImage }
    })
  },
  { immediate: true, deep: true },
)

function onPick(event: Event) {
  error.value = ''
  const input = event.target as HTMLInputElement
  const picked = Array.from(input.files || [])
  const next = [...files.value]
  for (const file of picked) {
    if (!ALLOWED_EXT.test(file.name)) {
      error.value = 'Allowed: jpg, png, gif, webp, pdf, xls, xlsx.'
      continue
    }
    if (file.size > MAX_BYTES) {
      error.value = 'Each file must be 10 MB or smaller.'
      continue
    }
    if (next.length >= props.maxFiles) {
      error.value = `At most ${props.maxFiles} files.`
      break
    }
    next.push(file)
  }
  files.value = next
  inputKey.value += 1
}

function removeAt(index: number) {
  const next = [...files.value]
  next.splice(index, 1)
  files.value = next
}
</script>

<template>
  <div class="attach">
    <label class="label">{{ label }}</label>
    <input
      :key="inputKey"
      type="file"
      accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.xls,.xlsx,image/*,application/pdf,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      multiple
      @change="onPick"
    />
    <p class="hint muted">
      Up to {{ maxFiles }} files, 10 MB each (images, PDF, Excel).
    </p>
    <p v-if="error" class="err">{{ error }}</p>
    <div v-if="previews.length" class="thumbs">
      <div v-for="(p, i) in previews" :key="p.name + i" class="thumb">
        <img v-if="p.isImage" :src="p.url" :alt="p.name" />
        <div v-else class="file-chip">{{ p.name }}</div>
        <button type="button" class="btn btn-ghost" @click="removeAt(i)">Remove</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.attach {
  margin-bottom: 1rem;
}
.label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
}
.hint {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
}
.err {
  color: var(--danger);
  font-size: 0.85rem;
  margin: 0.35rem 0 0;
}
.thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.75rem;
}
.thumb {
  width: 120px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.thumb img {
  width: 96px;
  height: 96px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
}
.file-chip {
  font-size: 0.75rem;
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  word-break: break-all;
  min-height: 96px;
}
.thumb .btn {
  padding: 0.2rem 0.4rem;
  font-size: 0.75rem;
}
</style>
