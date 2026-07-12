<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'

import { useMoodStore } from '@/stores/mood'
import { EMOTIONS, type Emotion } from '@/services/mood'
import { useKeystrokeCapture } from '@/composables/useKeystrokeCapture'

const store = useMoodStore()
const { current, history, loading, error } = storeToRefs(store)

const userId = ref(1)
const text = ref('')
const showEmotionPicker = ref(false)
const capture = useKeystrokeCapture()

async function submit() {
  if (!text.value.trim()) return
  await store.ingest(userId.value, {
    text: text.value,
    keydown_times: [...capture.keydownTimes.value],
    backspace_count: capture.backspaceCount.value,
    response_latency_s: capture.responseLatency(),
    is_followup: false,
    followup_depth: 0,
  })
  text.value = ''
  capture.reset()
  showEmotionPicker.value = false
}

async function confirm(ok: boolean) {
  if (ok) {
    await store.feedback(userId.value, true)
    showEmotionPicker.value = false
  } else {
    showEmotionPicker.value = true
  }
}

async function correctWith(emo: Emotion) {
  await store.feedback(userId.value, false, emo)
  showEmotionPicker.value = false
}

function pct(v: number): string {
  return `${Math.round(v * 100)}%`
}
</script>

<template>
  <main class="mood">
    <h1>NOEMA — tracciamento emotivo</h1>
    <p class="disclaimer">
      Prototipo di ricerca, non uno strumento diagnostico. Le stime sono inferenze da proxy
      comportamentali (testo, tempi di digitazione), non letture certe dello stato reale.
    </p>

    <label class="profile">
      Profilo utente (id):
      <input v-model.number="userId" type="number" min="1" />
    </label>

    <textarea
      v-model="text"
      rows="3"
      placeholder="Scrivi un messaggio…"
      @keydown="capture.onKeydown"
    ></textarea>
    <button :disabled="loading || !text.trim()" @click="submit">
      {{ loading ? 'Analizzo…' : 'Analizza' }}
    </button>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="current" class="result">
      <p class="label">{{ current.label }}</p>

      <ul class="bars">
        <li v-for="e in EMOTIONS" :key="e">
          <span class="bars__name">{{ e }}</span>
          <span class="bars__track"><span class="bars__fill" :style="{ width: pct(current.emotions[e]) }" /></span>
          <span class="bars__val">{{ pct(current.emotions[e]) }}</span>
        </li>
      </ul>

      <p class="pad">
        V={{ current.valence.toFixed(2) }} · A={{ current.arousal.toFixed(2) }} ·
        D={{ current.dominance.toFixed(2) }} · confidenza {{ pct(current.confidence) }}
      </p>

      <div class="feedback">
        <span>È corretto?</span>
        <button @click="confirm(true)">Sì</button>
        <button @click="confirm(false)">No</button>
      </div>
      <div v-if="showEmotionPicker" class="picker">
        <button v-for="e in EMOTIONS" :key="e" @click="correctWith(e)">{{ e }}</button>
      </div>
    </section>

    <section class="history">
      <button @click="store.loadHistory(userId)">Aggiorna storico</button>
      <ol>
        <li v-for="t in history" :key="t.id">
          #{{ t.id }} —
          <template v-if="t.dominant_emotions.length">
            {{ t.dominant_emotions[0][0] }} ({{ pct(t.dominant_emotions[0][1]) }})
          </template>
          <template v-else>neutro</template>
        </li>
      </ol>
    </section>
  </main>
</template>

<style scoped>
.mood {
  max-width: 680px;
  margin: 2rem auto;
  padding: 0 1rem;
}
.disclaimer {
  font-size: 0.85rem;
  color: #666;
}
.profile input {
  width: 5rem;
  margin-left: 0.5rem;
}
textarea {
  width: 100%;
  margin: 1rem 0 0.5rem;
  font: inherit;
  padding: 0.5rem;
}
.error {
  color: #b00;
}
.result {
  margin-top: 1.5rem;
  border-top: 1px solid #eee;
  padding-top: 1rem;
}
.label {
  font-size: 0.9rem;
  line-height: 1.4;
}
.bars {
  list-style: none;
  padding: 0;
}
.bars li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.2rem 0;
}
.bars__name {
  width: 6.5rem;
  font-size: 0.85rem;
}
.bars__track {
  flex: 1;
  height: 0.7rem;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}
.bars__fill {
  display: block;
  height: 100%;
  background: #6b8afd;
}
.bars__val {
  width: 3rem;
  text-align: right;
  font-size: 0.8rem;
}
.feedback,
.picker {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 0.75rem;
}
button {
  cursor: pointer;
}
</style>
