# Pulse Gate integrations

Each adapter demonstrates the same loop. Pulse with fewer than two charges to see recovery feedback. Charge twice, pulse to open the gate, then reset to play again.

| Target | Start | Verification |
| --- | --- | --- |
| Swift | From `swift/demo`, run `swift run PulseGate` with Swift 6. macOS 15+ opens a window. Other Swift targets use the console loop. | `swift test` verifies rules. |
| SpriteKit | On macOS 15+, choose SpriteKit in the Swift demo. | Exercise the loop in the SpriteKit view. |
| RealityKit | On macOS 15+, choose RealityKit in the Swift demo. | Exercise the loop in the RealityKit view. |
| Unity | Open `unity` with Unity 6. Choose **Beyin-Bedava → Open Pulse Gate** and enter Play mode. | `Unity -batchmode -nographics -quit -projectPath "$PWD/unity" -executeMethod PulseGateSmoke.Run -logFile -` from this directory. |
| Godot | `godot --path godot` (Godot 4.x). | `godot --headless --path godot -- --self-test` presses the actual scene buttons. |
| Three.js | From `threejs`, run `npm ci`, then `npm run dev`. | `npm test`, `npm run build`, then open the served URL with `?self-test` and verify `document.body.dataset.smoke === "pass"`. |
| Flutter | From `flutter-flame/demo`, run `flutter pub get` and `flutter run -d chrome` with Flutter 3.29.3 (Dart 3.7.2). | `flutter test` presses the Flutter controls around a Flame canvas. |

The exercises cover one small mechanic, so device input, performance, accessibility and game feel require additional tests in the adopting game. See the [release evidence](../../../benchmarks/REPORT.md) for executed checks.
