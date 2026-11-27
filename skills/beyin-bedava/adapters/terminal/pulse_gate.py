#!/usr/bin/env python3
"""A playable terminal example with a versioned JSON evidence exporter."""
import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Gate:
    charge: int = 0
    opened: bool = False

    def play(self, action):
        if action == "reset":
            self.charge, self.opened = 0, False
            return "Gate reset."
        if self.opened:
            return "Gate is already open."
        if action == "charge":
            self.charge = min(2, self.charge + 1)
            return f"Charge {self.charge}/2."
        if action == "pulse":
            if self.charge != 2:
                return "Pulse blocked. Charge the gate twice."
            self.charge, self.opened = 0, True
            return "Gate open."
        return "Choose charge, pulse, reset or quit."


def exercise():
    gate = Gate()
    gate.play("pulse")
    blocked = not gate.opened and gate.charge == 0
    gate.play("charge")
    gate.play("charge")
    gate.play("pulse")
    opened = gate.opened and gate.charge == 0
    gate.play("reset")
    return {"blocked": blocked, "opened": opened, "reset_charge": gate.charge, "reset_opened": gate.opened}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--revision")
    args = parser.parse_args()
    if args.plan:
        if not args.revision:
            parser.error("--plan requires --revision")
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if not any(check["id"] == "pulse_flow" for check in plan["checks"]):
            parser.error("plan must select the pulse_flow check")
        print(json.dumps({"version": 1, "plan_id": plan["plan_id"], "revision": args.revision,
                          "source": "runtime", "checks": [{"id": "pulse_flow", "observed": exercise(),
                                                            "artifact": "terminal gate exercise"}]}, indent=2))
        return

    gate = Gate()
    print("Pulse Gate. Type charge, pulse, reset or quit.")
    while True:
        try:
            action = input("> ").strip().lower()
        except EOFError:
            break
        if action == "quit":
            break
        print(gate.play(action))


if __name__ == "__main__":
    main()
