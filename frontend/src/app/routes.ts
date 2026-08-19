export type AppView =
  | { name: 'list' }
  | { name: 'profile' }
  | { name: 'settings' }
  | { name: 'play' }
  | { name: 'game'; id: string }

export function viewFromLocation(): AppView {
  const hash = window.location.hash.replace(/^#\/?/, '')
  const [name, id] = hash.split('/')
  if (name === 'profile') return { name: 'profile' }
  if (name === 'settings') return { name: 'settings' }
  if (name === 'play') return { name: 'play' }
  if (name === 'game' && id) return { name: 'game', id: decodeURIComponent(id) }
  return { name: 'list' }
}

export function hashForView(view: AppView): string {
  if (view.name === 'profile') return '#/profile'
  if (view.name === 'settings') return '#/settings'
  if (view.name === 'play') return '#/play'
  if (view.name === 'game') return `#/game/${encodeURIComponent(view.id)}`
  return '#/games'
}
