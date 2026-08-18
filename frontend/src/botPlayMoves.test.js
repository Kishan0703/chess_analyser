import assert from 'node:assert/strict'
import test from 'node:test'

import { buildBotMovePayload } from './botPlayMoves.js'

test('builds server move payload from react-chessboard v5 drop args', () => {
  assert.deepEqual(
    buildBotMovePayload({
      piece: { pieceType: 'p' },
      sourceSquare: 'e2',
      targetSquare: 'e4',
    }),
    { from: 'e2', to: 'e4', promotion: undefined },
  )
})

test('promotes pawns to queen on the final rank', () => {
  assert.deepEqual(
    buildBotMovePayload({
      piece: { pieceType: 'p' },
      sourceSquare: 'e7',
      targetSquare: 'e8',
    }),
    { from: 'e7', to: 'e8', promotion: 'q' },
  )
})

test('rejects drops without a target square', () => {
  assert.equal(
    buildBotMovePayload({
      piece: { pieceType: 'p' },
      sourceSquare: 'e2',
      targetSquare: null,
    }),
    null,
  )
})
