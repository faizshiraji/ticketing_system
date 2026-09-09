<script setup lang="ts">
import type { TicketStatus } from '@/types'
import { TICKET_STATUSES } from '@/types'

const props = defineProps<{
  status: TicketStatus
  breached?: boolean
}>()

const label = TICKET_STATUSES.find((s) => s.value === props.status)?.label ?? props.status
</script>

<template>
  <span class="wrap">
    <span class="badge" :data-status="status">{{ label }}</span>
    <span v-if="breached" class="badge breach">SLA breached</span>
  </span>
</template>

<style scoped>
.wrap {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #eef2f6;
  color: var(--ink-muted);
}

.badge[data-status='open'],
.badge[data-status='reopened'] {
  background: var(--info-soft);
  color: var(--info);
}

.badge[data-status='received'] {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge[data-status='in_progress'] {
  background: var(--accent-soft);
  color: var(--accent);
}

.badge[data-status='on_hold'] {
  background: var(--warn-soft);
  color: var(--warn);
}

.badge[data-status='resolved'],
.badge[data-status='closed'] {
  background: var(--ok-soft);
  color: var(--ok);
}

.breach {
  background: var(--danger-soft);
  color: var(--danger);
}
</style>
