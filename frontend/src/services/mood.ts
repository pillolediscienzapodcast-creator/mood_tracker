import { api } from '@/services/api'

export const EMOTIONS = [
  'gioia', 'fiducia', 'paura', 'sorpresa',
  'tristezza', 'disgusto', 'rabbia', 'anticipazione',
] as const

export type Emotion = (typeof EMOTIONS)[number]

export interface TurnRead {
  id: number
  created_at: string
  emotions: Record<string, number>
  dominant_emotions: [string, number][]
  valence: number
  arousal: number
  dominance: number
  confidence: number
  label: string
  no_lexicon_match: boolean
}

export interface FeedbackRead {
  emotions: Record<string, number>
  dominant_emotions: [string, number][]
  valence: number
  arousal: number
  dominance: number
  label: string
  feedback_count: number
  consolidated: boolean
}

export interface TurnCreate {
  text: string
  keydown_times: number[]
  backspace_count: number
  response_latency_s: number
  is_followup: boolean
  followup_depth: number
  hour_of_day?: number | null
}

export const moodApi = {
  ingestTurn: (userId: number, body: TurnCreate) =>
    api.post<TurnRead>(`/users/${userId}/turns`, body),
  listTurns: (userId: number) => api.get<TurnRead[]>(`/users/${userId}/turns`),
  sendFeedback: (userId: number, turnId: number, corretto: boolean, emozione_corretta?: Emotion) =>
    api.post<FeedbackRead>(`/users/${userId}/turns/${turnId}/feedback`, {
      corretto,
      emozione_corretta: corretto ? null : emozione_corretta,
    }),
  diagnostics: (userId: number) => api.get<Record<string, unknown>>(`/users/${userId}/model`),
}
