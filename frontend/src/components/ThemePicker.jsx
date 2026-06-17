import { useEffect, useState } from 'react'
import { getStoredTheme, applyTheme } from '../theme.js'

// Swatch preview colors mirror the palettes defined in index.css.
const THEMES = [
  { id: 'midnight', name: 'Classic', bg: '#f6f8f6', accent: '#3a8045' },
  { id: 'walnut', name: 'Walnut', bg: '#f7f4ef', accent: '#9a6130' },
  { id: 'forest', name: 'Forest', bg: '#edf5ec', accent: '#2f7d46' },
  { id: 'royal', name: 'Royal', bg: '#f5f4fa', accent: '#6750a4' },
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
