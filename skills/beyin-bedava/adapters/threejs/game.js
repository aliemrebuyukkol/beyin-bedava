export const initial = Object.freeze({ charge: 0, opened: false, denied: false });

export function play(state, action) {
  if (action === 'reset') return initial;
  if (state.opened) return state;
  if (action === 'charge') return { ...state, charge: Math.min(2, state.charge + 1), denied: false };
  if (action === 'pulse' && state.charge === 2) return { charge: 0, opened: true, denied: false };
  if (action === 'pulse') return { ...state, denied: true };
  return state;
}

export function message(state) {
  if (state.opened) return 'Gate open!';
  if (state.denied) return 'Pulse needs 2 charges. Try charging first.';
  return `Charge ${state.charge} / 2`;
}
