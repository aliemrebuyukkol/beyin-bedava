extends RefCounted

const MIN_FRAME_SAMPLES := 30
const MAX_FRAME_SAMPLES := 128
const BLOCKS := [&"wall", &"gate_a", &"gate_b", &"one_way", &"needs_power", &"plate_required"]

var enabled := false
var by_level := {}
var pending_at := -1
var frame_ms: Array[float] = []


func set_enabled(value: bool) -> void:
	enabled = value
	if not enabled:
		pending_at = -1


func clear() -> void:
	by_level.clear()
	frame_ms.clear()
	pending_at = -1


func record(level: int, action: StringName, result: StringName, received_at: int) -> void:
	if not enabled:
		return
	var key := str(level + 1)
	if not by_level.has(key):
		by_level[key] = {"actions": 0, "blocked": 0, "hints": 0, "undos": 0, "resets": 0, "wins": 0}
	var row: Dictionary = by_level[key]
	row["actions"] += 1
	row["blocked"] += int(result in BLOCKS)
	row["hints"] += int(action == &"hint")
	row["undos"] += int(result == &"undo")
	row["resets"] += int(result == &"reset")
	row["wins"] += int(result == &"win")
	if pending_at < 0:
		pending_at = received_at


func frame_drawn() -> void:
	if not enabled or pending_at < 0:
		return
	var elapsed := (Time.get_ticks_usec() - pending_at) / 1000.0
	pending_at = -1
	if elapsed < 0.0 or elapsed > 2000.0:
		return
	if frame_ms.size() >= MAX_FRAME_SAMPLES:
		frame_ms.pop_front()
	frame_ms.append(elapsed)


func p95():
	if frame_ms.size() < MIN_FRAME_SAMPLES:
		return null
	var sorted := frame_ms.duplicate()
	sorted.sort()
	return sorted[ceili(sorted.size() * 0.95) - 1]


func report(source := "observed_local") -> Dictionary:
	return {
		"schema_version": 1,
		"source": source,
		"levels": by_level.duplicate(true),
		"render_feedback": {"samples_ms": frame_ms.duplicate(), "p95_ms": p95()},
	}
