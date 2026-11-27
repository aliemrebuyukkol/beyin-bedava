extends RefCounted

const ACTIONS = {
	&"up": Vector2i.UP, &"down": Vector2i.DOWN,
	&"left": Vector2i.LEFT, &"right": Vector2i.RIGHT,
}
const EMPTY_ECHO := Vector2i(-1, -1)

var rows: Array
var start := Vector2i.ZERO
var player := Vector2i.ZERO
var echo := EMPTY_ECHO
var history: Array[Vector4i] = []


func _init(layout: Array) -> void:
	rows = layout
	for y in range(rows.size()):
		var x: int = rows[y].find("S")
		if x >= 0:
			start = Vector2i(x, y)
			break
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
	history.clear()


func state_of(at: Vector2i, current_echo: Vector2i) -> Vector4i:
	return Vector4i(at.x, at.y, current_echo.x, current_echo.y)


func transition(state: Vector4i, action: StringName) -> Vector4i:
	var at := Vector2i(state.x, state.y)
	var current_echo := Vector2i(state.z, state.w)
	if action == &"echo":
		if not active_plate(at).is_empty():
			return state_of(at, at)
	elif ACTIONS.has(action):
		var target: Vector2i = at + ACTIONS[action]
		var cell := tile(target)
		if cell != "#" and (cell not in ["A", "B"] or open_gate(cell, current_echo)):
			return state_of(target, current_echo)
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
	var before := state_of(player, echo)
	var after := transition(before, action)
	if before == after:
		if action == &"echo":
			return &"already" if echo == player else &"plate_required"
		if ACTIONS.has(action):
			var blocked: String = tile(player + ACTIONS[action])
			return &"gate_a" if blocked == "A" else &"gate_b" if blocked == "B" else &"wall"
		return &"ignored"
	history.append(before)
	restore(after)
	if won():
		return &"win"
	return &"echo" if action == &"echo" else &"move"


func restore(state: Vector4i) -> void:
	player = Vector2i(state.x, state.y)
	echo = Vector2i(state.z, state.w)


func solution() -> Array[StringName]:
	var origin := state_of(player, echo)
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
