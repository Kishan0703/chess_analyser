import { useCallback, useEffect, useState } from 'react'
import GameList from '../components/GameList.jsx'
import GameView from '../components/GameView.jsx'
import BotPlay from '../components/BotPlay.jsx'
import Profile from '../components/Profile.jsx'
import Settings from '../components/Settings.jsx'
import ThemePicker from '../components/ThemePicker.jsx'
import { hashForView, viewFromLocation } from './routes'
import type { AppView } from './routes'

const NAV_ITEMS: Array<{ view: AppView; id: AppView['name']; icon: string; label: string }> = [
  { view: { name: 'list' }, id: 'list', icon: '♟', label: 'Your games' },
  { view: { name: 'profile' }, id: 'profile', icon: '↗', label: 'Training profile' },
  { view: { name: 'settings' }, id: 'settings', icon: '⚙', label: 'Settings' },
  { view: { name: 'play' }, id: 'play', icon: '▶', label: 'Play vs Bot' },
]

export default function App() {
  const [view, setView] = useState<AppView>(() => viewFromLocation())
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    window.history.replaceState(viewFromLocation(), '', hashForView(viewFromLocation()))
    const onPopState = () => setView(viewFromLocation())
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  const activeNav = view.name === 'game' ? 'list' : view.name

  const navigate = useCallback((nextView: AppView) => {
    const nextHash = hashForView(nextView)
    setView(nextView)
    if (window.location.hash !== nextHash) {
      window.history.pushState(nextView, '', nextHash)
    }
  }, [])

  return (
    <div className={`app-shell ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="sidebar-head">
          <button className="brand brand-button" onClick={() => navigate({ name: 'list' })} title="Home">
            <span className="brand-mark">♜</span>
            <span className="brand-copy">
              <span className="brand-name">ChessCoach</span>
              <span className="brand-tag">positional coaching</span>
            </span>
          </button>
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Open sidebar'}
            title={sidebarOpen ? 'Collapse sidebar' : 'Open sidebar'}
          >
            <span />
            <span />
            <span />
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
              onClick={() => navigate(item.view)}
              aria-current={activeNav === item.id ? 'page' : undefined}
            >
              <span className="nav-icon" aria-hidden>{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          {view.name === 'game' && (
            <button className="ghost-btn back-btn" onClick={() => navigate({ name: 'list' })}>Back to games</button>
          )}
          <ThemePicker />
        </div>
      </aside>

      <main className="shell-main">
        <div className="page">
          {view.name === 'list' && (
            <GameList onOpen={(id: string) => navigate({ name: 'game', id })} />
          )}
          {view.name === 'game' && <GameView gameId={view.id} />}
          {view.name === 'profile' && (
            <Profile onOpenGame={(id: string) => navigate({ name: 'game', id })} />
          )}
          {view.name === 'settings' && <Settings />}
          {view.name === 'play' && (
            <BotPlay onOpenGame={(id: string) => navigate({ name: 'game', id })} />
          )}
        </div>
      </main>
    </div>
  )
}
