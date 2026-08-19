import type { GameMove } from '../../types/api'

const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

interface CoachMoment {
  ply: number
  moment_type?: string
  title: string
  explanation: string
}

export interface CoachReport {
  opening_summary?: string
  key_moments?: CoachMoment[]
  takeaways?: string[]
}

export interface Theme {
  id: number | string
  slug: string
  severity?: string
  note?: string
}

export interface VariationRequest {
  ply: number
  baseFen?: string
  bestLineSans?: string[]
  playedUci?: string | null
  playedSan?: string
  momentType?: string
}

interface CoachPanelProps {
  coach: CoachReport | null
  themes: Theme[]
  moves: GameMove[]
  onJump: (ply: number) => void
  onVariation?: (request: VariationRequest) => void
}

export default function CoachPanel({ coach, themes, moves, onJump, onVariation }: CoachPanelProps) {
  if (!coach) return null
  const takeaways = coach.takeaways ?? []

  // Build a lookup so we can find the best_line and base FEN for any ply
  const moveByPly: Record<number, GameMove> = {}
  const fenByPly: Record<number, string> = {}
  if (moves) {
    moves.forEach((m) => {
      moveByPly[m.ply] = m
      fenByPly[m.ply] = m.fen_after
    })
  }

  const handleMomentClick = (m: CoachMoment) => {
    const gamePly = m.ply - 1  // position just before the moment's move
    onJump(gamePly)
    if (onVariation) {
      const baseFen = fenByPly[m.ply - 1] || START_FEN
      const moveData = moveByPly[m.ply]
      const bestLineSans = moveData?.best_line?.trim().split(/\s+/).filter(Boolean) || []
      const momentType = m.moment_type || (moveData?.classification === 'best' ? 'positive' : 'negative')
      onVariation({
        ply: m.ply,
        baseFen,
        bestLineSans,
        playedUci: moveData?.uci,
        playedSan: moveData?.san,
        momentType,
      })
    }
  }

  return (
    <div className="card coach-report-card">
      <h3>Coach's report</h3>
      {coach.opening_summary
        ? <p className="coach-summary">{coach.opening_summary}</p>
        : <p className="status-line" style={{ marginBottom: 8 }}>No opening summary — click a moment below to jump to it.</p>
      }

      {(coach.key_moments || []).map((m, i) => {
        // Determine type: prefer coach-supplied field, fall back to move classification
        const mtype = m.moment_type || (moveByPly[m.ply]?.classification === 'best' ? 'positive' : 'negative')
        return (
          <div
            key={i}
            className={`moment ${mtype === 'positive' ? 'positive' : ''}`}
            onClick={() => handleMomentClick(m)}
            title={mtype === 'negative' ? 'Click to see the best line (← → to step through)' : 'Click to jump to this position'}
          >
            <div className="m-title">
              {mtype === 'positive' ? '✓ ' : ''}{m.title}
            </div>
            <p>{m.explanation}</p>
            {mtype === 'negative' && moveByPly[m.ply]?.best_line && (
              <div className="best-line-hint">
                Best: {moveByPly[m.ply].best_line} · click to step through ←→
              </div>
            )}
          </div>
        )
      })}

      {themes?.length > 0 && (
        <div className="themes">
          {themes.map((t) => (
            <span key={t.id} className={`theme-chip ${t.severity || ''}`} title={t.note || ''}>
              {t.slug}
            </span>
          ))}
        </div>
      )}

      {takeaways.length > 0 && (
        <>
          <h3 style={{ marginTop: 14 }}>What to work on</h3>
          <ul className="takeaways">
            {takeaways.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        </>
      )}
    </div>
  )
}
