import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api.js'

function Stat({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-num">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export default function Profile({ onOpenGame }) {
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.profile().then(setProfile).catch((e) => setError(e.message))
  }, [])

  const themeData = useMemo(() => (profile?.themes || []).slice(0, 8), [profile])

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
  const hasData = s.games > 0

  return (
    <div className="profile-page">
      <div className="page-head">
        <div>
          <p className="eyebrow">Training profile</p>
          <h2>Recurring patterns</h2>
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
          Import games, run engine analysis, and generate coaching to build your profile.
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
              </p>
            </div>

            <div className="card profile-card">
              <h3>Top themes</h3>
              {themeData.length ? (
                <div className="theme-chart">
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={themeData} layout="vertical" margin={{ left: 12, right: 12 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" allowDecimals={false} />
                      <YAxis dataKey="slug" type="category" width={132} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="var(--accent)" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="status-line">Generate coaching on analyzed games to collect themes.</p>
              )}
            </div>
          </div>

          <div className="card">
            <h3>Openings to review</h3>
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

          <div className="card">
            <h3>Recent analyzed games</h3>
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
        </>
      )}
    </div>
  )
}
