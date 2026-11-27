import GameCore
import XCTest

final class GateTests: XCTestCase {
    func testPulseRequiresTwoChargesAndResetClearsProgress() {
        var gate = Gate()
        gate.play(.pulse)
        XCTAssertTrue(gate.denied)
        gate.play(.charge)
        gate.play(.charge)
        gate.play(.charge)
        XCTAssertEqual(gate.charge, 2)
        gate.play(.pulse)
        XCTAssertTrue(gate.opened)
        XCTAssertEqual(gate.charge, 0)
        gate.play(.reset)
        XCTAssertEqual(gate, Gate())
    }
}
