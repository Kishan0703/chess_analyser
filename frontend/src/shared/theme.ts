export type ThemeId = 'classic' | 'slate'

export function getStoredTheme(): ThemeId {
  const stored = localStorage.getItem('cc-theme')
  if (stored === 'slate') return stored
  return 'classic'
}

export function applyTheme(id: ThemeId = getStoredTheme()): void {
  document.documentElement.dataset.theme = id
  localStorage.setItem('cc-theme', id)
}
