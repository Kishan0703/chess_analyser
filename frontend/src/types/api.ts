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

export interface GameDetail extends GameSummary {
  pgn: string
  moves: GameMove[]
  coach: unknown | null
  themes: unknown[]
}

export interface SettingsPayload {
  anthropic_api_key?: string | boolean | null
  gemini_api_key?: string | boolean | null
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

export interface JobStatus {
  status: 'not_started' | 'started' | 'already_running' | 'running' | 'done' | 'error'
  done?: number
  total?: number
  label?: string
  error?: string
}
