import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/services/api'

interface HealthResponse {
  status: string
}

export type BackendStatus = 'unknown' | 'checking' | 'online' | 'offline'

export const useHealthStore = defineStore('health', () => {
  const status = ref<BackendStatus>('unknown')

  async function checkHealth(): Promise<void> {
    status.value = 'checking'
    try {
      const data = await api.get<HealthResponse>('/health')
      status.value = data.status === 'ok' ? 'online' : 'offline'
    } catch {
      status.value = 'offline'
    }
  }

  return { status, checkHealth }
})
