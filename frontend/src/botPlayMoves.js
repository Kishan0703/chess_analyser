import { Chess } from 'chess.js'

export function buildBotMovePayload({ piece, sourceSquare, targetSquare } = {}) {
  if (!sourceSquare || !targetSquare) return null
  const promotion = piece?.pieceType?.toLowerCase() === 'p' &&
    (targetSquare.endsWith('8') || targetSquare.endsWith('1')) ? 'q' : undefined
  return {
    from: sourceSquare,
    to: targetSquare,
    promotion,
  }
}

export function previewBotPlayerMove(session, move) {
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
}) {
  const submitMove = async (drop) => {
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
    } catch (e) {
      setSession(session)
      setError(e.message)
      return false
    } finally {
      setBusy(false)
    }
  }

  return (drop) => {
    const session = getSession()
    if (!session || getBusy() || session.status !== 'active') return false
    const move = buildBotMovePayload(drop)
    const accepted = Boolean(move && previewBotPlayerMove(session, move))
    if (accepted) void submitMove(drop)
    return accepted
  }
}
