import { defineStore } from 'pinia'
import { ref } from 'vue'

import { moodApi, type Emotion, type TurnCreate, type TurnRead } from '@/services/mood'

export const useMoodStore = defineStore('mood', () => {
  const current = ref<TurnRead | null>(null)
  const history = ref<TurnRead[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const turnCount = ref(0)

  async function ingest(userId: number, body: TurnCreate): Promise<void> {
    loading.value = true
    error.value = null
    try {
      body.is_followup = turnCount.value > 0
      body.followup_depth = Math.min(turnCount.value, 5)
      current.value = await moodApi.ingestTurn(userId, body)
      turnCount.value += 1
    } catch {
      error.value = 'Errore durante la stima. Verifica che il profilo utente esista.'
    } finally {
      loading.value = false
    }
  }

  async function feedback(userId: number, corretto: boolean, emozione?: Emotion): Promise<void> {
    if (!current.value) return
    const res = await moodApi.sendFeedback(userId, current.value.id, corretto, emozione)
    // Aggiorna la stima corrente con lo stato corretto restituito.
    current.value = { ...current.value, ...res }
  }

  async function loadHistory(userId: number): Promise<void> {
    history.value = await moodApi.listTurns(userId)
  }

  return { current, history, loading, error, turnCount, ingest, feedback, loadHistory }
})
