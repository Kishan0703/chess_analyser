export function formatTimeControl(value: unknown): string {
  const raw = String(value || '').trim()
  if (!raw) return '-'
  if (raw.toLowerCase() === 'offline') return 'Offline'

  const [baseRaw, incrementRaw] = raw.split('+')
  const baseSeconds = Number(baseRaw)
  if (!Number.isFinite(baseSeconds)) return raw

  const baseMinutes = baseSeconds / 60
  const baseLabel = Number.isInteger(baseMinutes)
    ? String(baseMinutes)
    : `${Math.round(baseMinutes * 10) / 10}`

  if (incrementRaw == null || incrementRaw === '') {
    return `${baseLabel} min`
  }

  const increment = Number(incrementRaw)
  return Number.isFinite(increment) ? `${baseLabel}+${increment}` : raw
}
