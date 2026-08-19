import { useMemo, useState } from 'react'
import { Chessboard } from 'react-chessboard'
import { api } from '../api/chesscoach'
import { createBotDropHandler } from '../botPlayMoves.js'

const PRESETS = {
  beginner: { label: 'Beginner', skill_level: 2, move_time_ms: 80, randomness: 0.55 },
  casual: { label: 'Casual', skill_level: 5, move_time_ms: 150, randomness: 0.35 },
  club: { label: 'Club', skill_level: 8, move_time_ms: 1500, randomness: 0.2 },
  strong: { label: 'Strong', skill_level: 13, move_time_ms: 500, randomness: 0.08 },
  master: { label: 'Master', skill_level: 18, move_time_ms: 900, randomness: 0 },
}

const DIFFICULTY_HINTS = {
  beginner: 'Forgiving',
  casual: 'Light practice',
  club: 'Balanced',
  strong: 'Sharper play',
  master: 'Low randomness',
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
  const [notice, setNotice] = useState('')
  const moves = useMemo(() => movesFromPgn(session?.pgn || ''), [session?.pgn])

  const selectDifficulty = (nextDifficulty) => {
    setDifficulty(nextDifficulty)
    setAdvanced(PRESETS[nextDifficulty])
  }

  const startGame = async () => {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const next = await api.createBotGame({ player_color: playerColor, difficulty, advanced })
      setSession(next)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const onPieceDrop = useMemo(() => createBotDropHandler({
    getSession: () => session,
    getBusy: () => busy,
    setBusy,
    setError,
    setSession,
    playBotMove: api.playBotMove,
  }), [busy, session])

  const saveAndAnalyze = async () => {
    if (!session || session.status !== 'finished') return
    setBusy(true)
    setNotice('')
    try {
      if (session.saved_game_id || session.game_id) {
        onOpenGame(session.saved_game_id || session.game_id)
        return
      }
      const result = await api.saveBotGame(session.id)
      onOpenGame(result.game_id)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const resignGame = async () => {
    if (!session || session.status !== 'active') return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const next = await api.resignBotGame(session.id)
      setSession(next)
      setNotice('Game saved after resignation.')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const offerDraw = async () => {
    if (!session || session.status !== 'active') return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const next = await api.offerBotDraw(session.id)
      setSession(next)
      setNotice(next.draw_offer === 'accepted'
        ? 'Draw accepted. Game saved.'
        : 'Draw offer declined.')
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
  const statusText = error || notice || status

  return (
    <section className="bot-play">
      <div className="section-head">
        <div>
          <p className="eyebrow">Offline practice</p>
          <h1>Play vs Bot</h1>
        </div>
        <div className={`status-line bot-status ${error ? 'error' : ''}`}>{statusText}</div>
      </div>

      {!session ? (
        <div className="bot-setup">
          <div className="bot-controls card">
          <div className="bot-setup-head">
            <h2>New game</h2>
            <span>{PRESETS[difficulty].label} · {advanced.move_time_ms} ms/move</span>
          </div>
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
                  <span className="choice-title">{color[0].toUpperCase() + color.slice(1)}</span>
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
                  <span className="choice-title">{preset.label}</span>
                  <span className="choice-hint">{DIFFICULTY_HINTS[key]}</span>
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
              Start game
            </button>
          </div>
          </div>
        </div>
      ) : (
        <div className="bot-play-board-layout">
          <div className="bot-board">
            <div className="board-shell">
              <div className="board-stage">
                <Chessboard
                  options={{
                    position: session.fen,
                    boardOrientation: session.player_color || playerColor,
                    onPieceDrop,
                    allowDragging: Boolean(!busy && session.status === 'active'),
                    animationDurationInMs: 180,
                    showAnimations: true,
                    boardStyle: { width: '100%', height: '100%' },
                    id: 'bot-play-board',
                  }}
                />
              </div>
            </div>

            <div className="bot-actions bot-game-actions">
              <button type="button" className="secondary-action" onClick={startGame} disabled={busy}>
                New game
              </button>
              {session.status === 'active' && (
                <>
                  <button type="button" className="secondary-action" onClick={offerDraw} disabled={busy}>
                    Offer draw
                  </button>
                  <button type="button" className="danger-action" onClick={resignGame} disabled={busy}>
                    Resign
                  </button>
                </>
              )}
              {session.status === 'finished' && (
                <button type="button" className="primary-action" onClick={saveAndAnalyze} disabled={busy}>
                  {session.saved_game_id || session.game_id ? 'Open analysis' : 'Save and analyze'}
                </button>
              )}
            </div>

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
          </div>
        </div>
      )}
    </section>
  )
}
