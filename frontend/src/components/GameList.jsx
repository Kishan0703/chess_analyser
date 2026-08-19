import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/chesscoach'
import Onboarding from './Onboarding.jsx'
import InfoTip from './InfoTip.jsx'
import { formatTimeControl } from '../timeControl.js'

const PAGE_SIZE = 20

function outcome(game) {
  if (!game.user_color || game.result === '1/2-1/2') return 'draw'
  return (game.user_color === 'white') === (game.result === '1-0') ? 'win' : 'loss'
}

function resultLabel(game) {
  const o = outcome(game)
  return o === 'draw' ? '½–½' : o === 'win' ? 'Win' : 'Loss'
}

export default function GameList({ onOpen }) {
  const [games, setGames] = useState([])
  const [username, setUsername] = useState('')
  const [months, setMonths] = useState(3)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [ob, setOb] = useState(null)
  const [dismissed, setDismissed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [resultFilter, setResultFilter] = useState('all')
  const [analysisFilter, setAnalysisFilter] = useState('all')
  const [page, setPage] = useState(1)

  const refresh = () => api.games().then(setGames)
    .catch((e) => setStatus(e.message)).finally(() => setLoading(false))
  const refreshOb = () => api.onboarding().then(setOb).catch(() => {})

  useEffect(() => {
    refresh()
    refreshOb()
    api.settings().then((s) => setUsername(s.chesscom_username || '')).catch(() => {})
  }, [])

  const doImport = async () => {
    setBusy(true)
    setStatus('Importing from chess.com…')
    try {
      await api.saveSettings({ chesscom_username: username })
      const r = await api.importGames(username, months)
      const partial = r.failed_archives
        ? ` ${r.failed_archives} archive month(s) were temporarily unavailable.`
        : ''
      setStatus(`Imported ${r.imported} new games (${r.skipped} already known) from ${r.archives} month(s).${partial}`)
      refresh()
      refreshOb()
    } catch (e) {
      setStatus(`Import failed: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  const stats = useMemo(() => {
    const s = { total: games.length, wins: 0, losses: 0, draws: 0, analyzed: 0, coached: 0 }
    for (const g of games) {
      if (g.engine_analyzed) s.analyzed++
      if (g.coached) s.coached++
      const o = outcome(g)
      if (o === 'win') s.wins++; else if (o === 'loss') s.losses++; else s.draws++
    }
    return s
  }, [games])

  const filteredGames = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return games.filter((g) => {
      const o = outcome(g)
      if (resultFilter !== 'all' && o !== resultFilter) return false
      if (analysisFilter === 'coached' && !g.coached) return false
      if (analysisFilter === 'engine' && (!g.engine_analyzed || g.coached)) return false
      if (analysisFilter === 'unreviewed' && g.engine_analyzed) return false
      if (!needle) return true
      const haystack = [
        g.white, g.black, g.opening, g.eco, g.time_control, formatTimeControl(g.time_control), g.result,
        (g.played_at || '').slice(0, 10),
      ].filter(Boolean).join(' ').toLowerCase()
      return haystack.includes(needle)
    })
  }, [analysisFilter, games, query, resultFilter])

  const pageCount = Math.max(1, Math.ceil(filteredGames.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount)
  const pageStart = (currentPage - 1) * PAGE_SIZE
  const pageGames = filteredGames.slice(pageStart, pageStart + PAGE_SIZE)
  const showingStart = filteredGames.length ? pageStart + 1 : 0
  const showingEnd = Math.min(pageStart + PAGE_SIZE, filteredGames.length)

  const setupOk = ob && (
    ob.coach_provider === 'claude'
      ? ob.claude_key_set
      : ob.coach_provider === 'gemini'
        ? ob.gemini_key_set
        : (ob.ollama_reachable && ob.ollama_model_present)
  )
  const onboarded = ob && setupOk && ob.games > 0 && ob.coached > 0
  // ?welcome=1 forces the card open (for review/screenshots even when onboarded)
  const forceWelcome = typeof window !== 'undefined'
    && new URLSearchParams(window.location.search).has('welcome')
  const showOnboarding = ob && (forceWelcome || (!onboarded && !dismissed))

  return (
    <div>
      {showOnboarding && <Onboarding data={ob} onDismiss={() => setDismissed(true)} />}

      <div className="page-head">
        <div>
          <p className="eyebrow">Chess.com archive</p>
          <h2>Your games</h2>
          <p className="page-subtitle">Import, filter, and open games for engine analysis and coaching.</p>
        </div>
        {stats.total > 0 && (
          <div className="stats-strip">
            <div className="stat-card">
              <div className="stat-num">{stats.total}</div>
              <div className="stat-label">Games</div>
            </div>
            <div className="stat-card">
              <div className="stat-num">
                <span className="wl-w">{stats.wins}</span>
                <span className="wl-sep">–</span>
                <span className="wl-l">{stats.losses}</span>
                <span className="wl-sep">–</span>
                <span className="wl-d">{stats.draws}</span>
              </div>
              <div className="stat-label">W·L·D</div>
            </div>
            <div className="stat-card">
              <div className="stat-num">{stats.analyzed}</div>
              <div className="stat-label">Analyzed</div>
            </div>
            <div className="stat-card">
              <div className="stat-num">{stats.coached}</div>
              <div className="stat-label">Coached</div>
            </div>
          </div>
        )}
      </div>

      <div className="import-panel workspace-panel">
        <div className="import-copy">
          <span className="import-icon">♟</span>
          <div>
            <h3>Build your review queue</h3>
            <p>Pull recent games from Chess.com, then open any row to analyze key moments.</p>
          </div>
        </div>
        <div className="import-controls">
          <input
            placeholder="chess.com username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <select
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
            title="How far back to pull from your chess.com archive"
          >
            <option value={1}>last month</option>
            <option value={3}>last 3 months</option>
            <option value={6}>last 6 months</option>
            <option value={12}>last 12 months</option>
          </select>
          <button className="primary" onClick={doImport} disabled={busy || !username}>
            {busy ? 'Importing…' : 'Import games'}
          </button>
        </div>
        <span className={`status-line import-status ${status.startsWith('Import failed') ? 'error' : ''}`}>
          {status || 'Ready when your username is set.'}
        </span>
      </div>

      <div className="table-toolbar">
        <div className="toolbar-copy">
          <h3>Project library</h3>
          <span>
            {showingStart}-{showingEnd} of {filteredGames.length} shown
            {filteredGames.length !== games.length ? ` · ${games.length} total` : ''}
          </span>
        </div>
        <div className="toolbar-controls">
          <input
            placeholder="Search player, opening, date..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setPage(1)
            }}
            aria-label="Search games"
          />
          <select
            value={resultFilter}
            onChange={(e) => {
              setResultFilter(e.target.value)
              setPage(1)
            }}
            aria-label="Filter result"
          >
            <option value="all">All results</option>
            <option value="win">Wins</option>
            <option value="loss">Losses</option>
            <option value="draw">Draws</option>
          </select>
          <select
            value={analysisFilter}
            onChange={(e) => {
              setAnalysisFilter(e.target.value)
              setPage(1)
            }}
            aria-label="Filter analysis status"
          >
            <option value="all">All analysis</option>
            <option value="coached">Coached</option>
            <option value="engine">Engine only</option>
            <option value="unreviewed">Unreviewed</option>
          </select>
        </div>
      </div>

      <div className="game-table-wrap">
        <table className="game-table">
          <thead>
            <tr>
              <th>Date</th><th>White</th><th>Black</th><th>Result</th>
              <th>Opening</th><th>Time</th>
              <th>
                Analysis{' '}
                <InfoTip side="left">
                  <strong>—</strong> not analyzed yet · <strong>engine</strong> = Stockfish
                  evals &amp; move grades done · <strong>coached</strong> = positional report ready.
                </InfoTip>
              </th>
            </tr>
          </thead>
          <tbody>
            {loading && Array.from({ length: 6 }).map((_, i) => (
              <tr key={`sk${i}`} className="sk-tr">
                <td colSpan={7}><div className="skeleton sk-row" /></td>
              </tr>
            ))}
            {!loading && pageGames.map((g) => {
              const o = outcome(g)
              const youWhite = g.user_color === 'white'
              const youBlack = g.user_color === 'black'
              return (
                <tr key={g.id} className="row" onClick={() => onOpen(g.id)}>
                  <td>{(g.played_at || '').slice(0, 10)}</td>
                  <td className={youWhite ? 'you-name' : ''}>{g.white} {g.white_elo ? `(${g.white_elo})` : ''}</td>
                  <td className={youBlack ? 'you-name' : ''}>{g.black} {g.black_elo ? `(${g.black_elo})` : ''}</td>
                  <td><span className={`result-chip ${o}`}>{resultLabel(g)}</span></td>
                  <td>{(g.opening || g.eco || '').slice(0, 40)}</td>
                  <td>{formatTimeControl(g.time_control)}</td>
                  <td>
                    {g.coached ? <span className="pill done">Coached</span>
                      : g.engine_analyzed ? <span className="pill engine">Engine</span>
                      : <span className="pill">Open</span>}
                  </td>
                </tr>
              )
            })}
            {!loading && games.length === 0 && (
              <tr><td colSpan={7} className="status-line empty-state">No games yet. Import your chess.com archive above.</td></tr>
            )}
            {!loading && games.length > 0 && filteredGames.length === 0 && (
              <tr><td colSpan={7} className="status-line empty-state">No games match the current filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {!loading && filteredGames.length > PAGE_SIZE && (
        <div className="pagination-bar">
          <span>Page {currentPage} of {pageCount}</span>
          <div className="pagination-actions">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1}>
              Previous
            </button>
            <button className="primary" onClick={() => setPage((p) => Math.min(pageCount, p + 1))} disabled={currentPage === pageCount}>
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
