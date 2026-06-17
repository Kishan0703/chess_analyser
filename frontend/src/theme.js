export function getStoredTheme() {
  return localStorage.getItem('cc-theme') || 'midnight'
}

export function applyTheme(id = getStoredTheme()) {
  document.documentElement.dataset.theme = id
  localStorage.setItem('cc-theme', id)
}
