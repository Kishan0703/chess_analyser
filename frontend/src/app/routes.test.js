import assert from 'node:assert/strict'
import test from 'node:test'

import { hashForView, viewFromLocation } from './routes.ts'

test('maps supported hash routes to views and back', () => {
  const windowDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'window')
  Object.defineProperty(globalThis, 'window', {
    configurable: true,
    value: { location: { hash: '#/game/white%20vs%20black' } },
  })

  try {
    assert.deepEqual(viewFromLocation(), { name: 'game', id: 'white vs black' })
    assert.equal(hashForView({ name: 'game', id: 'white vs black' }), '#/game/white%20vs%20black')

    window.location.hash = '#/unknown'
    assert.deepEqual(viewFromLocation(), { name: 'list' })
  } finally {
    if (windowDescriptor) Object.defineProperty(globalThis, 'window', windowDescriptor)
    else delete globalThis.window
  }
})
