import { useEffect, useState } from 'react'
import { getStoredTheme, applyTheme } from '../theme.js'

const THEMES = [
  { id: 'classic', name: 'Classic', bg: '#f6f8f6', accent: '#3a8045' },
  { id: 'slate', name: 'Slate', bg: '#f2f5f2', accent: '#315f95' },
]

export default function ThemePicker() {
  const [theme, setTheme] = useState(getStoredTheme)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  const apply = (id) => {
    setTheme(id)
  }

  return (
    <div className="theme-picker" title="Color theme">
      <span className="theme-label">Theme</span>
      {THEMES.map((t) => (
        <button
          key={t.id}
          className={`swatch ${theme === t.id ? 'active' : ''}`}
          style={{ background: t.bg, color: t.accent }}
          onClick={() => apply(t.id)}
          title={`${t.name} theme`}
          aria-label={`${t.name} theme`}
          aria-pressed={theme === t.id}
        >
          <span className="swatch-dot" style={{ background: t.accent }} />
        </button>
      ))}
    </div>
  )
}
