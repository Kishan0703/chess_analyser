import { Chess } from 'chess.js'
import type { BotMoveRequest as BotMove, BotSession } from '../../types/api'

type BotDrop = {
  piece?: { pieceType?: string } | null
  sourceSquare?: string | null
  targetSquare?: string | null
}

type BotDropHandlerOptions = {
  getSession: () => BotSession | null
  getBusy: () => boolean
  setBusy: (value: boolean) => void
  setError: (value: string) => void
  setSession: (value: BotSession | ((current: BotSession) => BotSession)) => void
  playBotMove: (id: number, move: BotMove) => Promise<BotSession>
}

export function buildBotMovePayload({ piece, sourceSquare, targetSquare }: BotDrop = {}): BotMove | null {
  if (!sourceSquare || !targetSquare) return null
  const promotion = piece?.pieceType?.toLowerCase() === 'p'
    && (targetSquare.endsWith('8') || targetSquare.endsWith('1')) ? 'q' : undefined
  return {
    from: sourceSquare,
    to: targetSquare,
    promotion,
  }
}

export function previewBotPlayerMove(session: BotSession | null, move: BotMove): string | null {
  if (!session?.fen) return null
  const board = new Chess(session.fen)
  const next = board.move({
    from: move.from,
    to: move.to,
    promotion: move.promotion || 'q',
  })
  return next ? board.fen() : null
}

export function createBotDropHandler({
  getSession,
  getBusy,
  setBusy,
  setError,
  setSession,
  playBotMove,
}: BotDropHandlerOptions): (drop: BotDrop) => boolean {
  const submitMove = async (drop: BotDrop): Promise<boolean> => {
    const session = getSession()
    if (!session || getBusy() || session.status !== 'active') return false
    const move = buildBotMovePayload(drop)
    if (!move) return false
    const previewFen = previewBotPlayerMove(session, move)
    if (!previewFen) return false
    setBusy(true)
    setError('')
    setSession((current) => ({ ...current, fen: previewFen }))
    try {
      const next = await playBotMove(session.id, move)
      setSession(next)
      return true
    } catch (error) {
      setSession(session)
      setError((error as Error).message)
      return false
    } finally {
      setBusy(false)
    }
  }

  return (drop: BotDrop): boolean => {
    const session = getSession()
    if (!session || getBusy() || session.status !== 'active') return false
    const move = buildBotMovePayload(drop)
    const accepted = Boolean(move && previewBotPlayerMove(session, move))
    if (accepted) void submitMove(drop)
    return accepted
  }
}
