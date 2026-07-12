import { ref } from 'vue'

/**
 * Cattura i tempi di digitazione (analogo browser della cattura terminale
 * del prototipo): registra il timestamp assoluto (s) di ogni tasto premuto
 * nella textarea e conta i backspace. Vede SOLO gli eventi della textarea a
 * cui e' collegato, nient'altro. Misura anche la latenza di risposta (tempo
 * dal primo tasto all'invio).
 */
export function useKeystrokeCapture() {
  const keydownTimes = ref<number[]>([])
  const backspaceCount = ref(0)
  const firstKeyAt = ref<number | null>(null)

  function onKeydown(e: KeyboardEvent) {
    const t = performance.now() / 1000
    if (firstKeyAt.value === null) firstKeyAt.value = t
    if (e.key === 'Backspace') {
      backspaceCount.value += 1
      keydownTimes.value.pop()
    } else if (e.key.length === 1) {
      keydownTimes.value.push(t)
    }
  }

  function responseLatency(): number {
    if (firstKeyAt.value === null) return 0
    return performance.now() / 1000 - firstKeyAt.value
  }

  function reset() {
    keydownTimes.value = []
    backspaceCount.value = 0
    firstKeyAt.value = null
  }

  return { keydownTimes, backspaceCount, onKeydown, responseLatency, reset }
}
