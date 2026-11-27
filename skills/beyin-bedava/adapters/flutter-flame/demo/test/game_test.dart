import 'package:beyin_bedava_demo/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Pulse requires two charges and supports reset', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PulseGate()));
    Future<void> press(String action) async {
      await tester.tap(find.text(action));
      await tester.pump();
    }
    await press('Pulse');
    expect(find.textContaining('needs 2'), findsOneWidget);
    await press('Charge');
    await press('Charge');
    await press('Pulse');
    expect(find.text('Gate open!'), findsOneWidget);
    await press('Reset');
    expect(find.text('Charge 0 / 2'), findsOneWidget);
    await tester.pumpWidget(const SizedBox.shrink());
  });
}
