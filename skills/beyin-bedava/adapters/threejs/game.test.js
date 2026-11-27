import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initial, play } from './game.js';

test('pulse requires two charges, consumes them, and reset reopens the loop', () => {
  assert.equal(play(initial, 'pulse').denied, true);
  const charged = play(play(initial, 'charge'), 'charge');
  assert.equal(play(charged, 'charge').charge, 2);
  const won = play(charged, 'pulse');
  assert.deepEqual(won, { charge: 0, opened: true, denied: false });
  assert.equal(play(won, 'charge'), won);
  assert.equal(play(won, 'reset'), initial);
});
