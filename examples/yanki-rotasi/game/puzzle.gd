extends RefCounted

const ACTIONS = {
	&"up": Vector2i.UP, &"down": Vector2i.DOWN,
	&"left": Vector2i.LEFT, &"right": Vector2i.RIGHT,
}
const EMPTY_ECHO := Vector2i(-1, -1)

var rows: Array
var plates: Array[Vector2i] = []
var start := Vector2i.ZERO
var player := Vector2i.ZERO
var echo := EMPTY_ECHO
var battery := false
var history: Array[Vector4i] = []


func _init(layout: Array) -> void:
	rows = layout
	for y in range(rows.size()):
		for x in range(rows[y].length()):
			var at := Vector2i(x, y)
			if tile(at) == "S":
				start = at
			elif not active_plate(at).is_empty():
				plates.append(at)
	player = start


func tile(at: Vector2i) -> String:
	if at.x < 0 or at.y < 0 or at.y >= rows.size() or at.x >= rows[at.y].length():
		return "#"
	return rows[at.y][at.x]


func active_plate(at: Vector2i) -> String:
	var cell := tile(at)
	return cell if cell in ["a", "b"] else ""


func open_gate(gate: String, at: Vector2i) -> bool:
	return active_plate(at) == gate.to_lower()


func won() -> bool:
	return tile(player) == "E"


func reset() -> void:
	player = start
	echo = EMPTY_ECHO
	battery = false
	history.clear()


func snapshot() -> Vector4i:
	return Vector4i(player.x, player.y, plates.find(echo), int(battery))


func echo_at(index: int) -> Vector2i:
	return EMPTY_ECHO if index < 0 else plates[index]


func blocked_by(target: Vector2i, direction: Vector2i, current_echo: Vector2i,
		powered: bool) -> StringName:
	match tile(target):
		"#":
			return &"wall"
		"A":
			return &"" if open_gate("A", current_echo) else &"gate_a"
		"B":
			return &"" if open_gate("B", current_echo) else &"gate_b"
		">":
			return &"" if direction == Vector2i.RIGHT else &"one_way"
		"X":
			return &"" if powered else &"needs_power"
	return &""


func transition(state: Vector4i, action: StringName) -> Vector4i:
	var at := Vector2i(state.x, state.y)
	if action == &"echo":
		var index := plates.find(at)
		if index >= 0:
			return Vector4i(at.x, at.y, index, state.w)
	elif ACTIONS.has(action):
		var direction: Vector2i = ACTIONS[action]
		var target := at + direction
		if blocked_by(target, direction, echo_at(state.z), bool(state.w)) == &"":
			return Vector4i(target.x, target.y, state.z, int(bool(state.w) or tile(target) == "k"))
	return state


func play(action: StringName) -> StringName:
	if action == &"reset":
		reset()
		return &"reset"
	if action == &"undo":
		if history.is_empty():
			return &"empty"
		restore(history.pop_back())
		return &"undo"
	if won():
		return &"complete"
	var before := snapshot()
	var after := transition(before, action)
	if before == after:
		if action == &"echo":
			return &"already" if echo == player else &"plate_required"
		if ACTIONS.has(action):
			var direction: Vector2i = ACTIONS[action]
			return blocked_by(player + direction, direction, echo, battery)
		return &"ignored"
	history.append(before)
	restore(after)
	if won():
		return &"win"
	if before.w != after.w:
		return &"power"
	return &"echo" if action == &"echo" else &"move"


func restore(state: Vector4i) -> void:
	player = Vector2i(state.x, state.y)
	echo = echo_at(state.z)
	battery = bool(state.w)


func solution() -> Array[StringName]:
	var origin := snapshot()
	var frontier: Array[Vector4i] = [origin]
	var parents := {origin: origin}
	var incoming := {}
	var actions: Array = ACTIONS.keys()
	actions.append(&"echo")
	var cursor := 0
	while cursor < frontier.size():
		var current := frontier[cursor]
		cursor += 1
		if tile(Vector2i(current.x, current.y)) == "E":
			var route: Array[StringName] = []
			while current != origin:
				route.push_front(incoming[current])
				current = parents[current]
			return route
		for action in actions:
			var next := transition(current, action)
			if not parents.has(next):
				parents[next] = current
				incoming[next] = action
				frontier.append(next)
	return []
