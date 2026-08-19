import type { GameMove } from '../../types/api'

const BADGES: Record<string, string> = {
  brilliant: '‼',
  great: '!',
  best: '★',
  good: '✓',
  inaccuracy: '?!',
  mistake: '?',
  blunder: '??',
}

interface MoveProps {
  move?: GameMove
  currentPly: number
  onSelect: (ply: number) => void
}

interface MoveListProps {
  moves: GameMove[]
  currentPly: number
  onSelect: (ply: number) => void
}

interface MoveRow {
  num: number
  white: GameMove
  black?: GameMove
}

function Move({ move, currentPly, onSelect }: MoveProps) {
  if (!move) return <span />
  const badge = BADGES[move.classification ?? '']
  return (
    <span
      className={`move ${move.ply === currentPly ? 'current' : ''}`}
      onClick={() => onSelect(move.ply)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect(move.ply)
        }
      }}
    >
      {move.san}
      {badge && <span className={`badge ${move.classification}`}>{badge}</span>}
    </span>
  )
}

export default function MoveList({ moves, currentPly, onSelect }: MoveListProps) {
  const rows: MoveRow[] = []
  for (let i = 0; i < moves.length; i += 2) {
    rows.push({ num: i / 2 + 1, white: moves[i], black: moves[i + 1] })
  }
  return (
    <div className="moves">
      {rows.map((r) => (
        <FragmentRow key={r.num} row={r} currentPly={currentPly} onSelect={onSelect} />
      ))}
    </div>
  )
}

function FragmentRow({ row, currentPly, onSelect }: { row: MoveRow } & Pick<MoveListProps, 'currentPly' | 'onSelect'>) {
  return (
    <>
      <span className="num">{row.num}.</span>
      <Move move={row.white} currentPly={currentPly} onSelect={onSelect} />
      <Move move={row.black} currentPly={currentPly} onSelect={onSelect} />
    </>
  )
}
