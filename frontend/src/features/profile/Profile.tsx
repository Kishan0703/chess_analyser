import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/chesscoach'

interface ProfileProps {
  onOpenGame: (id: number | string) => void
}

interface ProfileSummary {
  games: number
  analyzed: number
  coached: number
  avg_win_pct_loss: number
  wins: number
  losses: number
  draws: number
  unknown_results?: number
  blunders: number
  mistakes: number
  inaccuracies: number
}

interface ThemeStat {
  slug: string
  count: number
}

interface OpeningStat {
  opening: string
  games: number
  wins: number
  losses: number
  draws: number
  avg_loss: number
}

interface RecentGame {
  game_id: number | string
  played_at?: string
  opponent: string
  result: string
  blunders: number
  mistakes: number
  themes: string[]
}

interface ProfileData {
  summary: ProfileSummary
  themes: ThemeStat[]
  openings: OpeningStat[]
  recent: RecentGame[]
}

interface StatProps {
  label: string
  value: string | number
}

interface InsightListProps {
  title: string
  items: string[]
  tone: string
}

const errorMessage = (error: unknown) => error instanceof Error ? error.message : String(error)

function Stat({ label, value }: StatProps) {
  return (
    <div className="stat-card">
      <div className="stat-num">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

function InsightList({ title, items, tone }: InsightListProps) {
  return (
    <div className={`profile-insight ${tone}`}>
      <h3>{title}</h3>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  )
}

export default function Profile({ onOpenGame }: ProfileProps) {
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.profile()
      .then((data) => setProfile(data as ProfileData))
      .catch((error: unknown) => setError(errorMessage(error)))
  }, [])

  const themeData = useMemo(() => (profile?.themes || []).slice(0, 8), [profile])
  const maxThemeCount = useMemo(
    () => Math.max(...themeData.map((theme) => theme.count), 1),
    [themeData],
  )

  if (error) return <div className="status-line error">{error}</div>
  if (!profile) {
    return (
      <div className="profile-page">
        <div className="skeleton" style={{ height: 120, borderRadius: 8 }} />
        <div className="skeleton" style={{ height: 320, borderRadius: 8 }} />
      </div>
    )
  }

  const s = profile.summary
  const hasData = s.analyzed > 0
  const topTheme = profile.themes?.[0]
  const topOpening = profile.openings?.[0]
  const strengths = [
    s.coached > 0 ? `${s.coached} coached game${s.coached === 1 ? '' : 's'} with strategic themes saved.` : null,
    s.avg_win_pct_loss <= 8 ? `Average loss is ${s.avg_win_pct_loss}%, which suggests steady conversion habits.` : null,
    s.wins > s.losses ? `Positive sample record: ${s.wins}-${s.losses}-${s.draws}.` : null,
  ].filter((item): item is string => Boolean(item))
  const focusAreas = [
    s.blunders > 0 ? `Reduce blunders first: ${s.blunders} found across analyzed games.` : null,
    s.mistakes > 0 ? `Review mistake positions: ${s.mistakes} medium-severity swings.` : null,
    topTheme ? `Recurring theme: ${topTheme.slug} appeared ${topTheme.count} time${topTheme.count === 1 ? '' : 's'}.` : null,
    topOpening ? `Opening to review: ${topOpening.opening} (${topOpening.games} game${topOpening.games === 1 ? '' : 's'}).` : null,
  ].filter((item): item is string => Boolean(item))

  return (
    <div className="profile-page">
      <div className="page-head">
        <div>
          <p className="eyebrow">Training profile</p>
          <h2>Recurring patterns</h2>
          <p className="page-subtitle">Turn analyzed games into a short study queue.</p>
        </div>
        <div className="stats-strip">
          <Stat label="Games" value={s.games} />
          <Stat label="Analyzed" value={s.analyzed} />
          <Stat label="Coached" value={s.coached} />
          <Stat label="Avg loss" value={`${s.avg_win_pct_loss}%`} />
        </div>
      </div>

      {!hasData && (
        <div className="card empty-profile">
          {s.games
            ? 'Run engine analysis on an imported game to build your profile.'
            : 'Import games, run engine analysis, and generate coaching to build your profile.'}
        </div>
      )}

      {hasData && (
        <>
          <div className="profile-grid">
            <div className="card profile-card">
              <h3>Move quality</h3>
              <div className="quality-list">
                <span>Blunders <strong>{s.blunders}</strong></span>
                <span> mistakes <strong>{s.mistakes}</strong></span>
                <span> inaccuracies <strong>{s.inaccuracies}</strong></span>
              </div>
              <p className="status-line">
                Record: {s.wins} wins, {s.losses} losses, {s.draws} draws.
                {s.unknown_results ? ` ${s.unknown_results} unknown.` : ''}
              </p>
            </div>

            <div className="card profile-card">
              <h3>Top themes</h3>
              {themeData.length ? (
                <ol className="theme-rank-list" aria-label="Top recurring themes">
                  {themeData.map((theme) => {
                    const pct = Math.max(10, Math.round((theme.count / maxThemeCount) * 100))
                    return (
                      <li key={theme.slug} className="theme-rank-row">
                        <div className="theme-rank-meta">
                          <span className="theme-rank-name">{theme.slug}</span>
                          <span className="theme-rank-count">{theme.count}</span>
                        </div>
                        <div
                          className="theme-rank-track"
                          role="img"
                          aria-label={`${theme.slug}: ${theme.count}`}
                        >
                          <span className="theme-rank-fill" style={{ width: `${pct}%` }} />
                        </div>
                      </li>
                    )
                  })}
                </ol>
              ) : (
                <p className="status-line">Generate coaching on analyzed games to collect themes.</p>
              )}
            </div>
          </div>

          <div className="profile-insight-grid">
            <InsightList
              title="Strengths"
              tone="strength"
              items={strengths.length ? strengths : ['Analyze and coach more games to identify reliable strengths.']}
            />
            <InsightList
              title="Focus areas"
              tone="focus"
              items={focusAreas.length ? focusAreas : ['No recurring weaknesses yet. Add more analyzed games to build a clearer queue.']}
            />
          </div>

          <div className="card">
            <h3>Openings to review</h3>
            <div className="profile-table-wrap">
              <table className="game-table compact-table">
                <thead>
                  <tr><th>Opening</th><th>Games</th><th>W-L-D</th><th>Avg loss</th></tr>
                </thead>
                <tbody>
                  {profile.openings.map((o) => (
                    <tr key={o.opening}>
                      <td>{o.opening}</td>
                      <td>{o.games}</td>
                      <td>{o.wins}-{o.losses}-{o.draws}</td>
                      <td>{o.avg_loss}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <h3>Recent analyzed games</h3>
            <div className="profile-table-wrap">
              <table className="game-table compact-table">
                <thead>
                  <tr><th>Date</th><th>Opponent</th><th>Result</th><th>Errors</th><th>Themes</th></tr>
                </thead>
                <tbody>
                  {profile.recent.map((g) => (
                    <tr key={g.game_id} className="row" onClick={() => onOpenGame(g.game_id)}>
                      <td>{(g.played_at || '').slice(0, 10)}</td>
                      <td>{g.opponent}</td>
                      <td>{g.result}</td>
                      <td>{g.blunders} blunders, {g.mistakes} mistakes</td>
                      <td>{g.themes.join(', ') || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
