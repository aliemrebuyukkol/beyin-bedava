// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "PulseGate",
    platforms: [.macOS(.v15)],
    products: [.executable(name: "PulseGate", targets: ["SwiftDemo"])],
    targets: [
        .target(name: "GameCore"),
        .executableTarget(name: "SwiftDemo", dependencies: ["GameCore"]),
        .testTarget(name: "GameCoreTests", dependencies: ["GameCore"])
    ]
)
