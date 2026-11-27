import 'dart:ui';
import 'package:flame/game.dart';
import 'package:flutter/material.dart';

void main() => runApp(const MaterialApp(home: PulseGate()));

class GateGame extends FlameGame {
  int charge = 0;
  bool opened = false;
  bool denied = false;

  String get status => opened
      ? 'Gate open!'
      : denied
          ? 'Pulse needs 2 charges. Try charging first.'
          : 'Charge $charge / 2';

  void play(String action) {
    if (action == 'Reset') {
      charge = 0;
      opened = denied = false;
    } else if (!opened && action == 'Charge') {
      if (charge < 2) charge++;
      denied = false;
    } else if (!opened && action == 'Pulse') {
      denied = charge < 2;
      opened = !denied;
      if (opened) charge = 0;
    }
  }

  @override
  void render(Canvas canvas) {
    super.render(canvas);
    canvas.drawRect(
      Rect.fromCenter(
        center: Offset(size.x / 2, size.y / 2),
        width: opened ? 16 : 100 + 30.0 * charge,
        height: 110,
      ),
      Paint()..color = opened ? const Color(0xff95dfa6) : const Color(0xff84c7ff),
    );
  }
}

class PulseGate extends StatefulWidget {
  const PulseGate({super.key});

  @override
  State<PulseGate> createState() => _PulseGateState();
}

class _PulseGateState extends State<PulseGate> {
  final game = GateGame();

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Pulse Gate')),
        body: Column(
          children: [
            Expanded(child: GameWidget(game: game)),
            Semantics(liveRegion: true, child: Text(game.status)),
            Wrap(children: [
              for (final action in ['Charge', 'Pulse', 'Reset'])
                TextButton(
                  onPressed: () => setState(() => game.play(action)),
                  child: Text(action),
                ),
            ]),
          ],
        ),
      );
}
