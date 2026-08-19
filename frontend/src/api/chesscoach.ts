import { request } from './client'
import type {
  BestLineResponse,
  BotGameCreateRequest,
  BotMoveRequest,
  BotSession,
  ChatRequest,
  ChatResponse,
  GameDetail,
  GameSummary,
  ImportGamesRequest,
  ImportGamesResponse,
  JobStatus,
  OnboardingResponse,
  PositionAnalysisResponse,
  PositionExplanationResponse,
  ProfileResponse,
  SaveBotGameResponse,
  SettingsPayload,
  SettingsUpdate,
} from '../types/api'

export const api = {
  settings: () => request<SettingsPayload>('/api/settings'),
  saveSettings: (settings: SettingsUpdate) =>
    request<SettingsPayload>('/api/settings', { method: 'PUT', body: JSON.stringify(settings) }),
  importGames: (payload: ImportGamesRequest) =>
    request<ImportGamesResponse>('/api/import', { method: 'POST', body: JSON.stringify(payload) }),
  games: () => request<GameSummary[]>('/api/games'),
  profile: () => request<ProfileResponse>('/api/profile'),
  onboarding: () => request<OnboardingResponse>('/api/onboarding'),
  game: (id: number) => request<GameDetail>(`/api/games/${id}`),
  analyze: (id: number) => request<JobStatus>(`/api/games/${id}/analyze`, { method: 'POST' }),
  analyzeStatus: (id: number) => request<JobStatus>(`/api/games/${id}/analyze/status`),
  coach: (id: number) => request<JobStatus>(`/api/games/${id}/coach`, { method: 'POST' }),
  coachStatus: (id: number) => request<JobStatus>(`/api/games/${id}/coach/status`),
  bestLine: (id: number, ply: number) => request<BestLineResponse>(`/api/games/${id}/bestline/${ply}`),
  positionAnalysis: (id: number, ply: number) =>
    request<PositionAnalysisResponse>(`/api/games/${id}/position/${ply}`),
  positionExplanation: (id: number, ply: number) =>
    request<PositionExplanationResponse>(`/api/games/${id}/position/${ply}/explanation`),
  createBotGame: (payload: BotGameCreateRequest) =>
    request<BotSession>('/api/play/bot/games', { method: 'POST', body: JSON.stringify(payload) }),
  getBotGame: (id: number) => request<BotSession>(`/api/play/bot/games/${id}`),
  playBotMove: (id: number, move: BotMoveRequest) =>
    request<BotSession>(`/api/play/bot/games/${id}/move`, { method: 'POST', body: JSON.stringify(move) }),
  saveBotGame: (id: number) => request<SaveBotGameResponse>(`/api/play/bot/games/${id}/save`, { method: 'POST' }),
  resignBotGame: (id: number) => request<BotSession>(`/api/play/bot/games/${id}/resign`, { method: 'POST' }),
  offerBotDraw: (id: number) => request<BotSession>(`/api/play/bot/games/${id}/draw-offer`, { method: 'POST' }),
  chat: (id: number, payload: ChatRequest) =>
    request<ChatResponse>(`/api/games/${id}/chat`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}
