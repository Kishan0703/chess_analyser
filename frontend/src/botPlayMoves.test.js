import assert from 'node:assert/strict'
import test from 'node:test'

import { buildBotMovePayload, createBotDropHandler } from './botPlayMoves.js'

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

test('drop handler sends the v5 drop payload to the bot move API', async () => {
  const calls = []
  let busy = false
  let session = {
    id: 42,
    status: 'active',
  }
  const handler = createBotDropHandler({
    getSession: () => session,
    getBusy: () => busy,
    setBusy: (value) => { busy = value },
    setError: () => {},
    setSession: (value) => { session = value },
    playBotMove: async (id, move) => {
      calls.push({ id, move })
      return { id, status: 'active', fen: 'after' }
    },
  })

  const accepted = handler({
    piece: { pieceType: 'p' },
    sourceSquare: 'e2',
    targetSquare: 'e4',
  })

  assert.equal(accepted, false)
  await new Promise((resolve) => setTimeout(resolve, 0))
  assert.deepEqual(calls, [{
    id: 42,
    move: { from: 'e2', to: 'e4', promotion: undefined },
  }])
  assert.equal(busy, false)
  assert.equal(session.fen, 'after')
})
