export type MoveClassification =
  | 'best'
  | 'great'
  | 'brilliant'
  | 'good'
  | 'inaccuracy'
  | 'mistake'
  | 'blunder'

export interface GameSummary {
  id: number
  white: string | null
  black: string | null
  white_elo: number | null
  black_elo: number | null
  result: string | null
  eco: string | null
  opening: string | null
  time_control: string | null
  played_at: string | null
  user_color: 'white' | 'black' | null
  engine_analyzed: 0 | 1 | boolean
  source: string
  source_url: string | null
  coached: 0 | 1 | boolean
}

export interface ImportGamesRequest {
  username: string
  months: number
}

export interface ImportGamesResponse {
  imported: number
  skipped: number
  archives: number
  failed_archives: number
}

export interface GameMove {
  game_id: number
  ply: number
  san: string
  uci: string
  fen_after: string
  eval_cp: number | null
  eval_mate: number | null
  best_uci: string | null
  best_san: string | null
  best_line: string | null
  classification: MoveClassification | string | null
  win_pct_loss: number | null
}

export interface CoachMoment {
  ply: number
  moment_type: 'positive' | 'negative' | string
  title: string
  explanation: string
}

export interface CoachTheme {
  slug: string
  side?: 'user' | 'opponent' | 'both' | null
  severity?: 'minor' | 'significant' | 'decisive' | string | null
  ply_start?: number | null
  ply_end?: number | null
  note?: string | null
}

export interface CoachReport {
  opening_summary: string
  key_moments: CoachMoment[]
  themes: CoachTheme[]
  takeaways: string[]
}

export interface GameTheme {
  id: number
  game_id: number
  slug: string
  side: 'user' | 'opponent' | 'both' | null
  severity: 'minor' | 'significant' | 'decisive' | string | null
  ply_start: number | null
  ply_end: number | null
  note: string | null
}

export interface GameDetail extends Omit<GameSummary, 'coached'> {
  pgn: string
  moves: GameMove[]
  coach: CoachReport | null
  themes: GameTheme[]
}

export interface SettingsPayload {
  anthropic_api_key?: boolean
  gemini_api_key?: boolean
  chesscom_username?: string | null
  claude_model?: string | null
  gemini_model?: string | null
  gemini_fallback_models?: string | null
  engine_movetime_ms?: number | null
  engine_multipv?: number | null
  engine_threads?: number | null
  stockfish_path?: string | null
  coach_provider?: string | null
  ollama_url?: string | null
  ollama_model?: string | null
}

export interface SettingsUpdate extends Omit<SettingsPayload, 'anthropic_api_key' | 'gemini_api_key'> {
  anthropic_api_key?: string | null
  gemini_api_key?: string | null
}

export interface JobStatus {
  status: 'not_started' | 'started' | 'already_running' | 'running' | 'done' | 'error'
  done?: number
  total?: number
  label?: string
  error?: string
}

export interface OnboardingResponse {
  coach_provider: string
  chesscom_username: string
  games: number
  engine_analyzed: number
  coached: number
  ollama_model: string | null
  ollama_reachable: boolean
  ollama_model_present: boolean
  claude_key_set: boolean
  gemini_key_set: boolean
  stockfish_path: string
  stockfish_found: boolean
  stockfish_error: string
}

export interface ProfileSummary {
  games: number
  analyzed: number
  coached: number
  wins: number
  losses: number
  draws: number
  unknown_results: number
  blunders: number
  mistakes: number
  inaccuracies: number
  avg_win_pct_loss: number
}

export interface MoveQualityStat {
  classification: MoveClassification | string
  count: number
}

export interface ProfileThemeStat {
  slug: string
  count: number
  decisive?: number
  significant?: number
  minor?: number
}

export interface ProfileOpeningStat {
  opening: string
  games: number
  wins: number
  losses: number
  draws: number
  avg_loss: number
}

export interface RecentProfileGame {
  game_id: number
  played_at: string | null
  opponent: string
  result: string
  blunders: number
  mistakes: number
  themes: string[]
}

export interface ProfileResponse {
  summary: ProfileSummary
  move_quality: MoveQualityStat[]
  themes: ProfileThemeStat[]
  openings: ProfileOpeningStat[]
  recent: RecentProfileGame[]
}

export interface BestLineResponse {
  fen: string
  sans: string[]
}

export interface PositionCandidate {
  move: string
  line: string
  eval_mate: number | null
  eval_cp: number | null
  white_win_pct: number | null
  side_to_move_win_pct: number | null
}

export interface PositionAnalysisResponse {
  fen: string
  ply: number
  side_to_move: 'white' | 'black'
  candidates: PositionCandidate[]
}

export interface PositionExplanationResponse {
  title: string
  explanation: string
  plan: string
  model: string | null
  input_tokens?: number
  output_tokens?: number
}

export type PlayerColor = 'white' | 'black'
export type BotDifficulty = 'beginner' | 'casual' | 'club' | 'strong' | 'master'

export interface BotAdvancedSettings {
  label?: string
  skill_level?: number
  move_time_ms?: number
  randomness?: number
}

export interface BotGameCreateRequest {
  player_color: PlayerColor
  difficulty: BotDifficulty
  advanced?: BotAdvancedSettings
}

export interface BotMoveRequest {
  from: string
  to: string
  promotion?: string | null
}

export interface BotMove {
  uci: string
  from: string
  to: string
  promotion: string | null
  san: string
}

export interface BotSession {
  id: number
  player_color: PlayerColor
  difficulty: BotDifficulty
  advanced: BotAdvancedSettings
  pgn: string
  fen: string
  status: 'active' | 'finished'
  result: string
  saved_game_id: number | null
  legal_moves: BotMove[]
  game_id?: number
  last_player_move?: BotMove
  last_bot_move?: BotMove
  draw_offer?: 'accepted' | 'declined'
  resigned?: boolean
}

export interface SaveBotGameResponse {
  game_id: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  question: string
  ply: number
  history: ChatMessage[]
}

export interface ChatResponse {
  answer: string
  model: string
  input_tokens: number
  output_tokens: number
}
