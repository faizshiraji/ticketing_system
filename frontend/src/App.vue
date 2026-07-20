<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import AppShell from '@/layouts/AppShell.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const { initialized, isAuthenticated } = storeToRefs(auth)
const route = useRoute()

const showShell = computed(() => initialized.value && isAuthenticated.value && route.name !== 'login')

onMounted(() => {
  void auth.bootstrap()
})
</script>

<template>
  <div v-if="!initialized" class="boot">Loading…</div>
  <AppShell v-else-if="showShell">
    <RouterView />
  </AppShell>
  <RouterView v-else />
</template>

<style scoped>
.boot {
  min-height: 100vh;
  display: grid;
  place-items: center;
  color: var(--ink-muted);
}
</style>
