<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: File[]
    maxFiles?: number
    label?: string
  }>(),
  {
    modelValue: () => [],
    maxFiles: 5,
    label: 'Images',
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

const previews = ref<{ name: string; url: string }[]>([])

watch(
  () => props.modelValue,
  (list) => {
    for (const p of previews.value) URL.revokeObjectURL(p.url)
    previews.value = list.map((f) => ({ name: f.name, url: URL.createObjectURL(f) }))
  },
  { immediate: true, deep: true },
)

function onPick(event: Event) {
  error.value = ''
  const input = event.target as HTMLInputElement
  const picked = Array.from(input.files || [])
  const next = [...files.value]
  for (const file of picked) {
    if (!file.type.startsWith('image/')) {
      error.value = 'Only image files are allowed (jpg, png, gif, webp).'
      continue
    }
    if (file.size > 5 * 1024 * 1024) {
      error.value = 'Each image must be 5 MB or smaller.'
      continue
    }
    if (next.length >= props.maxFiles) {
      error.value = `At most ${props.maxFiles} images.`
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
      accept="image/jpeg,image/png,image/gif,image/webp"
      multiple
      @change="onPick"
    />
    <p class="hint muted">Up to {{ maxFiles }} images, 5 MB each (jpg, png, gif, webp).</p>
    <p v-if="error" class="err">{{ error }}</p>
    <div v-if="previews.length" class="thumbs">
      <div v-for="(p, i) in previews" :key="p.url" class="thumb">
        <img :src="p.url" :alt="p.name" />
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
  width: 96px;
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
.thumb .btn {
  padding: 0.2rem 0.4rem;
  font-size: 0.75rem;
}
</style>
