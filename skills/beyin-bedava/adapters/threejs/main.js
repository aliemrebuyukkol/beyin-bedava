import * as THREE from 'three';
import { initial, message, play } from './game.js';

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(420, 260);
document.body.append(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x233847);
const camera = new THREE.PerspectiveCamera(45, 420 / 260, 0.1, 30);
camera.position.z = 6;
const gate = new THREE.Mesh(
  new THREE.BoxGeometry(2.2, 2.2, 0.35),
  new THREE.MeshNormalMaterial(),
);
scene.add(gate);
const status = document.querySelector('#status');
const buttons = [...document.querySelectorAll('button')];
let state = initial;

function render() {
  status.textContent = message(state);
  gate.rotation.y = state.opened ? Math.PI / 2 : state.charge * 0.15;
  renderer.render(scene, camera);
}

for (const button of buttons) {
  button.addEventListener('click', () => {
    state = play(state, button.textContent.toLowerCase());
    render();
  });
}
render();

if (new URLSearchParams(location.search).has('self-test')) {
  buttons[1].click();
  const denied = status.textContent.includes('needs 2');
  buttons[0].click();
  buttons[0].click();
  buttons[1].click();
  const won = status.textContent === 'Gate open!' && gate.rotation.y === Math.PI / 2;
  buttons[2].click();
  document.body.dataset.smoke = denied && won && status.textContent === 'Charge 0 / 2' ? 'pass' : 'fail';
}
