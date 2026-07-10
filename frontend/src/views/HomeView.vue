<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import { useHealthStore } from '@/stores/health'

const healthStore = useHealthStore()
const { status } = storeToRefs(healthStore)

const statusLabel = computed(() => {
  switch (status.value) {
    case 'online':
      return '🟢 Online'
    case 'offline':
      return '🔴 Offline'
    case 'checking':
      return '… checking'
    default:
      return '—'
  }
})

onMounted(() => {
  healthStore.checkHealth()
})
</script>

<template>
  <main class="home">
    <h1>Startup Template</h1>

    <section class="status">
      <span class="status__label">Backend status:</span>
      <span class="status__value">{{ statusLabel }}</span>
    </section>
  </main>
</template>

<style scoped>
.home {
  max-width: 640px;
  margin: 4rem auto;
  padding: 0 1rem;
}

.status {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status__value {
  font-weight: 600;
}
</style>
