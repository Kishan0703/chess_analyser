import { api } from './chesscoach'
import type {
  BestLineResponse,
  BotGameCreateRequest,
  BotMoveRequest,
  BotSession,
  ChatRequest,
  ChatResponse,
  GameDetail,
  ImportGamesRequest,
  ImportGamesResponse,
  JobStatus,
  OnboardingResponse,
  PositionAnalysisResponse,
  PositionExplanationResponse,
  ProfileResponse,
  SaveBotGameResponse,
} from '../types/api'

const importRequest: ImportGamesRequest = { username: 'chesscoach', months: 3 }
const botGameRequest: BotGameCreateRequest = {
  player_color: 'white',
  difficulty: 'club',
  advanced: { skill_level: 8, move_time_ms: 250, randomness: 0.2 },
}
const botMoveRequest: BotMoveRequest = { from: 'e2', to: 'e4' }
const chatRequest: ChatRequest = {
  question: 'What was the best plan?',
  ply: 12,
  history: [{ role: 'user', content: 'Why was this move inaccurate?' }],
}

const apiContracts = {
  importGames: api.importGames(importRequest) satisfies Promise<ImportGamesResponse>,
  profile: api.profile() satisfies Promise<ProfileResponse>,
  onboarding: api.onboarding() satisfies Promise<OnboardingResponse>,
  game: api.game(1) satisfies Promise<GameDetail>,
  coach: api.coach(1) satisfies Promise<JobStatus>,
  bestLine: api.bestLine(1, 12) satisfies Promise<BestLineResponse>,
  positionAnalysis: api.positionAnalysis(1, 12) satisfies Promise<PositionAnalysisResponse>,
  positionExplanation: api.positionExplanation(1, 12) satisfies Promise<PositionExplanationResponse>,
  createBotGame: api.createBotGame(botGameRequest) satisfies Promise<BotSession>,
  getBotGame: api.getBotGame(1) satisfies Promise<BotSession>,
  playBotMove: api.playBotMove(1, botMoveRequest) satisfies Promise<BotSession>,
  saveBotGame: api.saveBotGame(1) satisfies Promise<SaveBotGameResponse>,
  resignBotGame: api.resignBotGame(1) satisfies Promise<BotSession>,
  offerBotDraw: api.offerBotDraw(1) satisfies Promise<BotSession>,
  chat: api.chat(1, chatRequest) satisfies Promise<ChatResponse>,
}

void apiContracts
