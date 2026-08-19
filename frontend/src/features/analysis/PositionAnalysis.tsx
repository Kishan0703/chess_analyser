import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../../api/chesscoach'
import type { GameMove } from '../../types/api'

const LABELS: Record<string, string> = {
  brilliant: 'Brilliant',
  great: 'Great',
  best: 'Best',
  good: 'Good',
  inaccuracy: 'Inaccuracy',
  mistake: 'Mistake',
  blunder: 'Blunder',
}

interface Candidate {
  move: string
  line: string
  eval_mate?: number | null
  eval_cp?: number | null
  side_to_move_win_pct?: number | null
}

interface PositionData {
  side_to_move?: string
  candidates?: Candidate[]
}

interface Explanation {
  explanation?: string
  plan?: string
}

interface PositionAnalysisProps {
  gameId: number | string
  ply: number
  analyzed: boolean
  currentMove: GameMove | null
  onVariation: (request: {
    ply: number
    bestLineSans: string[]
    playedUci?: string | null
    playedSan?: string
    momentType: string
  }) => void
}

const errorMessage = (error: unknown) => error instanceof Error ? error.message : String(error)

function evalText(candidate?: Candidate) {
  if (!candidate) return '...'
  if (candidate.eval_mate != null) return `M${Math.abs(candidate.eval_mate)}`
  if (candidate.eval_cp == null) return '...'
  const pawns = candidate.eval_cp / 100
  return `${pawns >= 0 ? '+' : ''}${pawns.toFixed(2)}`
}

function verdictText(move: GameMove | null) {
  if (!move) return 'Start position. No move has been played yet.'
  const label = LABELS[move.classification ?? ''] || 'Move'
  if (['brilliant', 'great', 'best'].includes(move.classification ?? '')) {
    return `${label}: ${move.san} matched the engine's main idea.`
  }
  if (move.classification === 'good') {
    return `Good: ${move.san} kept the position healthy.`
  }
  const loss = Number(move.win_pct_loss || 0).toFixed(1)
  const best = move.best_san ? ` Stockfish preferred ${move.best_san}.` : ''
  return `${label}: ${move.san} gave away about ${loss}% win probability.${best}`
}

export default function PositionAnalysis({ gameId, ply, analyzed, currentMove, onVariation }: PositionAnalysisProps) {
  const [cache, setCache] = useState<Record<number, PositionData>>({})
  const [errors, setErrors] = useState<Record<number, string>>({})
  const [explanationCache, setExplanationCache] = useState<Record<number, Explanation>>({})
  const [explanationErrors, setExplanationErrors] = useState<Record<number, string>>({})
  const requestId = useRef(0)
  const explanationRequestId = useRef(0)
  const data = cache[ply]
  const error = errors[ply]
  const explanation = explanationCache[ply]
  const explanationError = explanationErrors[ply]

  useEffect(() => {
    if (!analyzed) return
    if (cache[ply]) return
    if (errors[ply]) return

    const id = ++requestId.current
    api.positionAnalysis(Number(gameId), ply)
      .then((result) => {
        if (requestId.current !== id) return
        setCache((prev) => ({ ...prev, [ply]: result as PositionData }))
      })
      .catch((error: unknown) => {
        if (requestId.current !== id) return
        setErrors((prev) => ({ ...prev, [ply]: errorMessage(error) }))
      })
  }, [analyzed, cache, errors, gameId, ply])

  useEffect(() => {
    if (!analyzed) return
    if (explanationCache[ply]) return
    if (explanationErrors[ply]) return

    const id = ++explanationRequestId.current
    const timer = setTimeout(() => {
      api.positionExplanation(Number(gameId), ply)
      .then((result) => {
        if (explanationRequestId.current !== id) return
        setExplanationCache((prev) => ({ ...prev, [ply]: result as Explanation }))
      })
      .catch((error: unknown) => {
        if (explanationRequestId.current !== id) return
        setExplanationErrors((prev) => ({ ...prev, [ply]: errorMessage(error) }))
      })
    }, 180)
    return () => clearTimeout(timer)
  }, [analyzed, explanationCache, explanationErrors, gameId, ply])

  const verdictClass = currentMove?.classification || 'neutral'
  const bestLineSans = useMemo(
    () => currentMove?.best_line?.trim().split(/\s+/).filter(Boolean) || [],
    [currentMove]
  )
  const canReplayBest = currentMove?.best_line && currentMove?.classification &&
    !['brilliant', 'great', 'best'].includes(currentMove.classification ?? '')
  const candidates = data?.candidates ?? []

  if (!analyzed) return null

  return (
    <div className="card position-analysis">
      <div className="position-analysis-head">
        <div>
          <h3>Current position</h3>
          <div className="status-line">
            {ply === 0 ? 'Before move 1' : `After ${currentMove?.san || `ply ${ply}`}`}
          </div>
        </div>
        <span className={`position-verdict ${verdictClass}`}>
          {currentMove ? (LABELS[currentMove.classification ?? ''] || currentMove.classification) : 'Start'}
        </span>
      </div>

      <div className="coach-insight">
        {explanation ? (
          <>
            <p>{explanation.explanation || verdictText(currentMove)}</p>
            {explanation.plan && <p className="coach-plan">{explanation.plan}</p>}
          </>
        ) : (
          <>
            {!explanationError && <div className="status-line">Preparing explanation...</div>}
          </>
        )}
        {explanationError && (
          <div className="status-line">
            Coach explanation unavailable: {explanationError}
          </div>
        )}
      </div>

      {canReplayBest && (
        <button
          className="line-button"
          onClick={() => onVariation({
            ply: currentMove.ply,
            bestLineSans,
            playedUci: currentMove.uci,
            playedSan: currentMove.san,
            momentType: 'negative',
          })}
        >
          Show best line: {currentMove.best_line}
        </button>
      )}

      <div className="candidate-title">
        Best moves now
        {data?.side_to_move && <span>{data.side_to_move} to move</span>}
      </div>
      {!data && !error && <div className="status-line">Analyzing this position...</div>}
      {error && <div className="error">{error}</div>}
      {candidates.length > 0 && (
        <div className="candidate-list">
          {candidates.map((candidate, i) => (
            <div className="candidate-row" key={`${candidate.move}-${i}`}>
              <div className="candidate-rank">{i + 1}</div>
              <div className="candidate-line">
                <strong>{candidate.move}</strong>
                <span>{candidate.line}</span>
              </div>
              <div className="candidate-score">
                <strong>{evalText(candidate)}</strong>
                {candidate.side_to_move_win_pct != null && (
                  <span>{candidate.side_to_move_win_pct}%</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
