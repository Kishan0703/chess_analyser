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
    setBusy(true)
    setError('')
    try {
      const next = await playBotMove(session.id, move)
      setSession(next)
      return true
    } catch (e) {
      setError(e.message)
      return false
    } finally {
      setBusy(false)
    }
  }

  return (drop) => {
    void submitMove(drop)
    return false
  }
}
