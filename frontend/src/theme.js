export function getStoredTheme() {
  const stored = localStorage.getItem('cc-theme')
  if (stored === 'slate') return stored
  return 'classic'
}

export function applyTheme(id = getStoredTheme()) {
  document.documentElement.dataset.theme = id
  localStorage.setItem('cc-theme', id)
}
