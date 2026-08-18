import { useMemo, useState } from 'react'
import { Chessboard } from 'react-chessboard'
import { api } from '../api.js'
import { buildBotMovePayload } from '../botPlayMoves.js'

const PRESETS = {
  beginner: { label: 'Beginner', skill_level: 2, move_time_ms: 80, randomness: 0.55 },
  casual: { label: 'Casual', skill_level: 5, move_time_ms: 150, randomness: 0.35 },
  club: { label: 'Club', skill_level: 8, move_time_ms: 250, randomness: 0.2 },
  strong: { label: 'Strong', skill_level: 13, move_time_ms: 500, randomness: 0.08 },
  master: { label: 'Master', skill_level: 18, move_time_ms: 900, randomness: 0 },
}

function movesFromPgn(pgn) {
  const sans = pgn
    .replace(/\[[^\]]*\]\s*/g, '')
    .trim()
    .split(/\s+/)
    .filter((token) => token && !/^\d+\.(\.\.)?$/.test(token) && !['*', '1-0', '0-1', '1/2-1/2'].includes(token))

  return Array.from({ length: Math.ceil(sans.length / 2) }, (_, index) => ({
    number: index + 1,
    white: sans[index * 2],
    black: sans[index * 2 + 1],
  }))
}

export default function BotPlay({ onOpenGame }) {
  const [playerColor, setPlayerColor] = useState('white')
  const [difficulty, setDifficulty] = useState('club')
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [advanced, setAdvanced] = useState(PRESETS.club)
  const [session, setSession] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const moves = useMemo(() => movesFromPgn(session?.pgn || ''), [session?.pgn])

  const selectDifficulty = (nextDifficulty) => {
    setDifficulty(nextDifficulty)
    setAdvanced(PRESETS[nextDifficulty])
  }

  const startGame = async () => {
    setBusy(true)
    setError('')
    try {
      const next = await api.createBotGame({ player_color: playerColor, difficulty, advanced })
      setSession(next)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const submitMove = async (drop) => {
    if (!session || busy || session.status !== 'active') return false
    const move = buildBotMovePayload(drop)
    if (!move) return false
    setBusy(true)
    setError('')
    try {
      const next = await api.playBotMove(session.id, move)
      setSession(next)
      return true
    } catch (e) {
      setError(e.message)
      return false
    } finally {
      setBusy(false)
    }
  }

  const onPieceDrop = (drop) => {
    void submitMove(drop)
    return false
  }

  const saveAndAnalyze = async () => {
    if (!session || session.status !== 'finished') return
    setBusy(true)
    try {
      const result = await api.saveBotGame(session.id)
      onOpenGame(result.game_id)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const updateAdvanced = (field, value) => {
    setAdvanced((current) => ({ ...current, [field]: value }))
  }

  const status = !session
    ? 'Ready to start'
    : session.status === 'finished'
      ? `Finished: ${session.result}`
      : busy
        ? 'Bot is thinking'
        : 'Active'

  return (
    <section className="bot-play">
      <div className="section-head">
        <div>
          <p className="eyebrow">Offline practice</p>
          <h1>Play vs Bot</h1>
        </div>
        <div className={`status-line bot-status ${error ? 'error' : ''}`}>{error || status}</div>
      </div>

      <div className="bot-play-layout">
        <div className="bot-board">
          <div className="board-shell">
            <div className="board-stage">
              <Chessboard
                options={{
                  position: session?.fen,
                  boardOrientation: session?.player_color || playerColor,
                  onPieceDrop,
                  allowDragging: Boolean(session && !busy && session.status === 'active'),
                  boardStyle: { width: '100%', height: '100%' },
                  id: 'bot-play-board',
                }}
              />
            </div>
          </div>

          {session && (
            <div className="card bot-move-list">
              <h3>Moves</h3>
              {moves.length > 0 ? (
                <div className="moves">
                  {moves.map((move) => (
                    <div className="bot-move-row" key={move.number}>
                      <span className="num">{move.number}.</span>
                      <span>{move.white}</span>
                      <span>{move.black}</span>
                    </div>
                  ))}
                </div>
              ) : <div className="bot-empty-moves">No moves yet</div>}
            </div>
          )}
        </div>

        <div className="bot-controls card">
          <div className="bot-control-group">
            <h3>Play as</h3>
            <div className="bot-choice-row" role="group" aria-label="Player color">
              {['white', 'black'].map((color) => (
                <button
                  type="button"
                  className={playerColor === color ? 'selected' : ''}
                  disabled={busy}
                  key={color}
                  onClick={() => setPlayerColor(color)}
                >
                  {color[0].toUpperCase() + color.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="bot-control-group">
            <h3>Difficulty</h3>
            <div className="difficulty-grid">
              {Object.entries(PRESETS).map(([key, preset]) => (
                <button
                  type="button"
                  className={difficulty === key ? 'selected' : ''}
                  disabled={busy}
                  key={key}
                  onClick={() => selectDifficulty(key)}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          <div className="bot-control-group">
            <button
              type="button"
              className="advanced-toggle"
              aria-expanded={advancedOpen}
              onClick={() => setAdvancedOpen((open) => !open)}
            >
              Advanced settings
            </button>
            {advancedOpen && (
              <div className="advanced-panel">
                <label>
                  Skill level
                  <input type="number" min="0" max="20" value={advanced.skill_level} disabled={busy}
                    onChange={(e) => updateAdvanced('skill_level', Number(e.target.value))} />
                </label>
                <label>
                  Move time (ms)
                  <input type="number" min="10" value={advanced.move_time_ms} disabled={busy}
                    onChange={(e) => updateAdvanced('move_time_ms', Number(e.target.value))} />
                </label>
                <label>
                  Randomness
                  <input type="number" min="0" max="1" step="0.01" value={advanced.randomness} disabled={busy}
                    onChange={(e) => updateAdvanced('randomness', Number(e.target.value))} />
                </label>
              </div>
            )}
          </div>

          <div className="bot-actions">
            <button type="button" className="primary-action" onClick={startGame} disabled={busy}>
              {session ? 'New game' : 'Start game'}
            </button>
            {session?.status === 'finished' && (
              <button type="button" className="secondary-action" onClick={saveAndAnalyze} disabled={busy}>
                Save and analyze
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
