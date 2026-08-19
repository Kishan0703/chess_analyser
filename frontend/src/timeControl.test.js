import assert from 'node:assert/strict'
import test from 'node:test'

import { formatTimeControl } from './timeControl.js'

test('formats raw chess.com time controls for display', () => {
  assert.equal(formatTimeControl('600'), '10 min')
  assert.equal(formatTimeControl('300+5'), '5+5')
  assert.equal(formatTimeControl('180+2'), '3+2')
  assert.equal(formatTimeControl('offline'), 'Offline')
  assert.equal(formatTimeControl(''), '-')
})
