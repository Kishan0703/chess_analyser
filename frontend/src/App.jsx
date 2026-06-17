import { useCallback, useEffect, useState } from 'react'
import GameList from './components/GameList.jsx'
import GameView from './components/GameView.jsx'
import Settings from './components/Settings.jsx'
import ThemePicker from './components/ThemePicker.jsx'

function viewFromLocation() {
  const hash = window.location.hash.replace(/^#\/?/, '')
  const [name, id] = hash.split('/')
  if (name === 'settings') return { name: 'settings' }
  if (name === 'game' && id) return { name: 'game', id: decodeURIComponent(id) }
  return { name: 'list' }
}

function hashForView(view) {
  if (view.name === 'settings') return '#/settings'
  if (view.name === 'game') return `#/game/${encodeURIComponent(view.id)}`
  return '#/games'
}

export default function App() {
  const [view, setView] = useState(() => viewFromLocation())

  useEffect(() => {
    window.history.replaceState(viewFromLocation(), '', hashForView(viewFromLocation()))
    const onPopState = () => setView(viewFromLocation())
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  const navigate = useCallback((nextView) => {
    const nextHash = hashForView(nextView)
    setView(nextView)
    if (window.location.hash !== nextHash) {
      window.history.pushState(nextView, '', nextHash)
    }
  }, [])

  return (
    <>
      <div className="topbar">
        <div className="brand" onClick={() => navigate({ name: 'list' })} title="Home">
          <span className="brand-mark">♞</span>
          <span className="brand-copy">
            <span className="brand-name">ChessCoach</span>
            <span className="brand-tag">play sharper positions</span>
          </span>
        </div>
        <div className="spacer" />
        {view.name !== 'list' && (
          <button className="ghost-btn" onClick={() => navigate({ name: 'list' })}>← Games</button>
        )}
        <ThemePicker />
        <button className="ghost-btn" onClick={() => navigate({ name: 'settings' })}>Settings</button>
      </div>
      <div className="page">
        {view.name === 'list' && (
          <GameList onOpen={(id) => navigate({ name: 'game', id })} />
        )}
        {view.name === 'game' && <GameView gameId={view.id} />}
        {view.name === 'settings' && <Settings />}
      </div>
    </>
  )
}
