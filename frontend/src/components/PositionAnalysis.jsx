import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api.js'

const LABELS = {
  brilliant: 'Brilliant',
  great: 'Great',
  best: 'Best',
  good: 'Good',
  inaccuracy: 'Inaccuracy',
  mistake: 'Mistake',
  blunder: 'Blunder',
}

function evalText(candidate) {
  if (!candidate) return '...'
  if (candidate.eval_mate != null) return `M${Math.abs(candidate.eval_mate)}`
  if (candidate.eval_cp == null) return '...'
  const pawns = candidate.eval_cp / 100
  return `${pawns >= 0 ? '+' : ''}${pawns.toFixed(2)}`
}

function verdictText(move) {
  if (!move) return 'Start position. No move has been played yet.'
  const label = LABELS[move.classification] || 'Move'
  if (['brilliant', 'great', 'best'].includes(move.classification)) {
    return `${label}: ${move.san} matched the engine's main idea.`
  }
  if (move.classification === 'good') {
    return `Good: ${move.san} kept the position healthy.`
  }
  const loss = Number(move.win_pct_loss || 0).toFixed(1)
  const best = move.best_san ? ` Stockfish preferred ${move.best_san}.` : ''
  return `${label}: ${move.san} gave away about ${loss}% win probability.${best}`
}

export default function PositionAnalysis({ gameId, ply, analyzed, currentMove, onVariation }) {
  const [cache, setCache] = useState({})
  const [errors, setErrors] = useState({})
  const requestId = useRef(0)
  const data = cache[ply]
  const error = errors[ply]

  useEffect(() => {
    if (!analyzed) return
    if (cache[ply]) return
    if (errors[ply]) return

    const id = ++requestId.current
    api.positionAnalysis(gameId, ply)
      .then((result) => {
        if (requestId.current !== id) return
        setCache((prev) => ({ ...prev, [ply]: result }))
      })
      .catch((e) => {
        if (requestId.current !== id) return
        setErrors((prev) => ({ ...prev, [ply]: e.message }))
      })
  }, [analyzed, cache, errors, gameId, ply])

  const verdictClass = currentMove?.classification || 'neutral'
  const bestLineSans = useMemo(
    () => currentMove?.best_line?.trim().split(/\s+/).filter(Boolean) || [],
    [currentMove]
  )
  const canReplayBest = currentMove?.best_line && currentMove?.classification &&
    !['brilliant', 'great', 'best'].includes(currentMove.classification)

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
          {currentMove ? (LABELS[currentMove.classification] || currentMove.classification) : 'Start'}
        </span>
      </div>

      <p className="position-verdict-text">{verdictText(currentMove)}</p>

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
      {data?.candidates?.length > 0 && (
        <div className="candidate-list">
          {data.candidates.map((candidate, i) => (
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
