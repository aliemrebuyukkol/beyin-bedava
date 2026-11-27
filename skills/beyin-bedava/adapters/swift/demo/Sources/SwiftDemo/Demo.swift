import GameCore

#if os(macOS)
import RealityKit
import SpriteKit
import SwiftUI

@main
struct PulseGateApp: App {
    var body: some Scene {
        WindowGroup("Pulse Gate") {
            GateView()
        }
    }
}

@MainActor
struct GateView: View {
    enum Engine: String, CaseIterable, Identifiable {
        case swift = "SwiftUI"
        case sprite = "SpriteKit"
        case reality = "RealityKit"

        var id: Self { self }
    }

    @State private var gate = Gate()
    @State private var engine = Engine.swift
    @State private var sprite = GateScene(size: CGSize(width: 380, height: 200))
    @State private var model = ModelEntity(
        mesh: .generateBox(size: 0.32),
        materials: [SimpleMaterial(color: .systemCyan, isMetallic: false)]
    )

    var body: some View {
        VStack(spacing: 16) {
            Picker("Renderer", selection: $engine) {
                ForEach(Engine.allCases) { option in
                    Text(option.rawValue).tag(option)
                }
            }
            .pickerStyle(.segmented)

            switch engine {
            case .swift:
                RoundedRectangle(cornerRadius: 8)
                    .fill(gate.opened ? .green : .cyan)
                    .frame(width: gate.opened ? 20 : CGFloat(110 + 30 * gate.charge), height: 110)
                    .frame(maxWidth: .infinity, minHeight: 200)
            case .sprite:
                SpriteView(scene: sprite).frame(height: 200)
                    .onAppear { sprite.update(gate) }
                    .onChange(of: gate) { _, value in sprite.update(value) }
            case .reality:
                RealityView { content in
                    content.add(model)
                } update: { _ in
                    model.scale.x = gate.opened ? 0.08 : 1 + 0.2 * Float(gate.charge)
                }
                .frame(height: 200)
            }

            Text(gate.status)
            HStack {
                Button("Charge") { gate.play(.charge) }
                Button("Pulse") { gate.play(.pulse) }
                Button("Reset") { gate.play(.reset) }
            }
        }
        .padding(24)
        .frame(minWidth: 420)
    }
}

@MainActor
final class GateScene: SKScene {
    private let shape = SKShapeNode(rectOf: CGSize(width: 110, height: 110), cornerRadius: 8)

    override func didMove(to view: SKView) {
        scaleMode = .aspectFit
        backgroundColor = .darkGray
        shape.position = CGPoint(x: size.width / 2, y: size.height / 2)
        if shape.parent == nil { addChild(shape) }
    }

    func update(_ gate: Gate) {
        shape.fillColor = gate.opened ? .green : .cyan
        shape.xScale = gate.opened ? 0.15 : 1 + 0.25 * CGFloat(gate.charge)
    }
}
#else
@main
struct PulseGateCLI {
    static func main() {
        var gate = Gate()
        print("Pulse Gate. Type charge, pulse, reset or quit.")
        print(gate.status)
        while let action = readLine() {
            switch action {
            case "charge": gate.play(.charge)
            case "pulse": gate.play(.pulse)
            case "reset": gate.play(.reset)
            case "quit": return
            default: print("Choose charge, pulse or reset.")
            }
            print(gate.status)
        }
    }
}
#endif
