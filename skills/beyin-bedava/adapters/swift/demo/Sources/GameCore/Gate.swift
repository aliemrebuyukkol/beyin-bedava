public struct Gate: Equatable {
    public enum Action { case charge, pulse, reset }

    public private(set) var charge = 0
    public private(set) var opened = false
    public private(set) var denied = false

    public init() {}

    public var status: String {
        if opened { return "Gate open!" }
        if denied { return "Pulse needs 2 charges. Try charging first." }
        return "Charge \(charge) / 2"
    }

    public mutating func play(_ action: Action) {
        if action == .reset {
            self = Gate()
            return
        }
        guard !opened else { return }
        switch action {
        case .charge:
            charge = min(2, charge + 1)
            denied = false
        case .pulse:
            denied = charge < 2
            opened = !denied
            if opened { charge = 0 }
        case .reset:
            break
        }
    }
}
