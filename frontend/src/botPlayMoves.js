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
