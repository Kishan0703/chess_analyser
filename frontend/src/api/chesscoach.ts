import { request } from './client'
import type { GameDetail, GameSummary, JobStatus, SettingsPayload } from '../types/api'

export const api = {
  settings: () => request<SettingsPayload>('/api/settings'),
  saveSettings: (settings: SettingsPayload) =>
    request<SettingsPayload>('/api/settings', { method: 'PUT', body: JSON.stringify(settings) }),
  importGames: (username: string, months: number) =>
    request<unknown>('/api/import', { method: 'POST', body: JSON.stringify({ username, months }) }),
  games: () => request<GameSummary[]>('/api/games'),
  profile: () => request<unknown>('/api/profile'),
  onboarding: () => request<unknown>('/api/onboarding'),
  game: (id: number) => request<GameDetail>(`/api/games/${id}`),
  analyze: (id: number) => request<JobStatus>(`/api/games/${id}/analyze`, { method: 'POST' }),
  analyzeStatus: (id: number) => request<JobStatus>(`/api/games/${id}/analyze/status`),
  coach: (id: number) => request<unknown>(`/api/games/${id}/coach`, { method: 'POST' }),
  coachStatus: (id: number) => request<JobStatus>(`/api/games/${id}/coach/status`),
  bestLine: (id: number, ply: number) => request<unknown>(`/api/games/${id}/bestline/${ply}`),
  positionAnalysis: (id: number, ply: number) => request<unknown>(`/api/games/${id}/position/${ply}`),
  positionExplanation: (id: number, ply: number) =>
    request<unknown>(`/api/games/${id}/position/${ply}/explanation`),
  createBotGame: (payload: unknown) =>
    request<unknown>('/api/play/bot/games', { method: 'POST', body: JSON.stringify(payload) }),
  getBotGame: (id: number) => request<unknown>(`/api/play/bot/games/${id}`),
  playBotMove: (id: number, move: unknown) =>
    request<unknown>(`/api/play/bot/games/${id}/move`, { method: 'POST', body: JSON.stringify(move) }),
  saveBotGame: (id: number) => request<unknown>(`/api/play/bot/games/${id}/save`, { method: 'POST' }),
  resignBotGame: (id: number) => request<unknown>(`/api/play/bot/games/${id}/resign`, { method: 'POST' }),
  offerBotDraw: (id: number) => request<unknown>(`/api/play/bot/games/${id}/draw-offer`, { method: 'POST' }),
  chat: (id: number, question: string, ply: number, history: unknown) =>
    request<unknown>(`/api/games/${id}/chat`, {
      method: 'POST',
      body: JSON.stringify({ question, ply, history }),
    }),
}
