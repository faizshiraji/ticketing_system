<script setup lang="ts">
import type { Category, Priority, TicketStatus } from '@/types'
import { TICKET_STATUSES } from '@/types'

defineProps<{
  status: TicketStatus | ''
  category: number | ''
  priority: number | ''
  categories: Category[]
  priorities: Priority[]
  showAssignedMine?: boolean
  assignedMine?: boolean
}>()

const emit = defineEmits<{
  'update:status': [value: TicketStatus | '']
  'update:category': [value: number | '']
  'update:priority': [value: number | '']
  'update:assignedMine': [value: boolean]
  apply: []
  reset: []
}>()
</script>

<template>
  <div class="filters card">
    <div class="field">
      <label for="filter-status">Status</label>
      <select
        id="filter-status"
        :value="status"
        @change="emit('update:status', ($event.target as HTMLSelectElement).value as TicketStatus | '')"
      >
        <option value="">All</option>
        <option v-for="s in TICKET_STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
    </div>
    <div class="field">
      <label for="filter-category">Category</label>
      <select
        id="filter-category"
        :value="category"
        @change="
          emit(
            'update:category',
            ($event.target as HTMLSelectElement).value
              ? Number(($event.target as HTMLSelectElement).value)
              : '',
          )
        "
      >
        <option value="">All</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>
    <div class="field">
      <label for="filter-priority">Priority</label>
      <select
        id="filter-priority"
        :value="priority"
        @change="
          emit(
            'update:priority',
            ($event.target as HTMLSelectElement).value
              ? Number(($event.target as HTMLSelectElement).value)
              : '',
          )
        "
      >
        <option value="">All</option>
        <option v-for="p in priorities" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>
    <label v-if="showAssignedMine" class="check field">
      <span>Assignment</span>
      <span class="check-row">
        <input
          type="checkbox"
          :checked="assignedMine"
          @change="emit('update:assignedMine', ($event.target as HTMLInputElement).checked)"
        />
        Assigned to me
      </span>
    </label>
    <div class="actions">
      <button type="button" class="btn" @click="emit('apply')">Apply</button>
      <button type="button" class="btn btn-secondary" @click="emit('reset')">Reset</button>
    </div>
  </div>
</template>

<style scoped>
.check span:first-child {
  font-size: 0.875rem;
  font-weight: 600;
}

.check-row {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 2.5rem;
  color: var(--ink-muted);
  font-size: 0.9rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
}
</style>
