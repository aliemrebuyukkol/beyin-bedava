extends RefCounted

const Puzzle = preload("res://game/puzzle.gd")
const Campaign = preload("res://game/levels.gd")
const Progress = preload("res://game/progress.gd")

var failures := 0


func check(condition: bool, message: String) -> void:
	if not condition:
		failures += 1
		push_error(message)


func run(game: Control) -> void:
	var audit := audit_campaign()
	if "--audit" in OS.get_cmdline_user_args():
		print(JSON.stringify(audit))
	else:
		await check_scene(game)
		if failures == 0:
			print("PASS · six levels, mobile layout, touch, keyboard, recovery, local metrics and save")
	game.get_tree().quit(int(failures > 0))


func audit_campaign() -> Dictionary:
	var previous := 0
	var layouts := {}
	var repetition_flags := 0
	var mechanic_sets := {}
	var entries := []
	var expected_routes := [9, 15, 23, 27, 32, 41]
	for index in range(Campaign.LEVELS.size()):
		var layout: Array = Campaign.LEVELS[index]["rows"]
		var cells := "".join(layout)
		var width: int = layout[0].length()
		check(cells.count("S") == 1 and cells.count("E") == 1, "Expected one start and exit.")
		for row in layout:
			check(row.length() == width, "Expected rectangular level.")
		var flipped := PackedStringArray(layout)
		flipped.reverse()
		var stamp := "\n".join(layout)

		var horizontally_mirrored: PackedStringArray = []
		for line in layout:
			horizontally_mirrored.append(line.reverse())
		var duplicate := (layouts.has(stamp) or layouts.has("\n".join(flipped))
			or layouts.has("\n".join(horizontally_mirrored)))
		repetition_flags += int(duplicate)
		check(not duplicate, "Duplicate or mirrored level.")
		layouts[stamp] = true
		var mechanics := ["echo"]
		for indicator in [">", "k", "B"]:
			if indicator in cells:
				mechanics.append(indicator)
		mechanic_sets[",".join(mechanics)] = true
		var model := Puzzle.new(layout)
		var route := model.solution()
		check(route.size() == expected_routes[index], "Shortest route changed.")
		check(index == 0 or (route.size() > previous and route.size() - previous <= 10),
			"Campaign pacing requires an increasing step of at most 10 actions.")
		for action in route:
			model.play(action)
		check(model.won(), "Solver route should win.")
		check(model.play(&"undo") == &"undo" and not model.won(), "Undo should recover the pre-win state.")
		model.play(&"reset")
		check(model.player == model.start and model.echo == Puzzle.EMPTY_ECHO and not model.battery,
			"Reset should clear state.")
		entries.append({"level": index + 1, "shortest_actions": route.size(), "mechanics": mechanics})
		previous = route.size()
	check(mechanic_sets.size() >= 4, "Expected four distinct mechanic sets.")
	var direction := Puzzle.new(["#######", "#S>.kE#", "#######"])
	check(direction.play(&"right") == &"move", "Entering the one-way tile from the west should work.")
	direction.play(&"right")
	check(direction.play(&"left") == &"one_way", "The same tile should reject entry from the east.")
	check(direction.play(&"right") == &"power" and direction.battery, "Power cell should be acquired.")
	direction.play(&"undo")
	check(not direction.battery, "Undo should clear the acquired power cell.")
	var power_gate := Puzzle.new(["######", "#SXkE#", "######"])
	check(power_gate.play(&"right") == &"needs_power", "Gate should require power.")
	return {"evidence_kind": "deterministic_gameplay_analysis", "levels": entries,
		"distinct_mechanic_sets": mechanic_sets.size(), "layout_repetition_flags": repetition_flags}


func resize_window(game: Control, dimensions: Vector2i) -> void:
	game.get_window().size = dimensions
	var scene_tree := game.get_tree()
	await scene_tree.process_frame
	await scene_tree.process_frame
	await scene_tree.process_frame


func touch(point: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.position = point
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func check_scene(game: Control) -> void:
	for dimensions in [Vector2i(320, 568), Vector2i(390, 844), Vector2i(844, 390), Vector2i(1080, 760)]:
		await resize_window(game, dimensions)
		check(game.size.is_equal_approx(Vector2(dimensions)), "Viewport size should track the test window.")
		check(game.columns.vertical == (dimensions.x < 650), "Incorrect responsive breakpoint.")
		for control in game.actions.values() + game.level_buttons:
			var bounds: Rect2 = control.get_global_rect()
			check(bounds.size.x >= 44 and bounds.size.y >= 44, "Touch targets must be at least 44x44.")
			check(bounds.position.x >= -0.1 and bounds.end.x <= dimensions.x + 0.1,
				"Controls must not overflow the viewport horizontally.")
		if dimensions == Vector2i(320, 568):
			check(game.actions[&"echo"].get_global_rect().end.y <= dimensions.y,
				"The main action must be visible on the shortest portrait viewport.")

	await resize_window(game, Vector2i(390, 844))
	check(game.level == 0 and game.level_buttons[1].disabled, "Level 1 should be initially accessible.")
	var right_button: Button = game.actions[&"right"]
	check(right_button.get_global_rect().end.y <= 844, "Primary direction control should be visible.")
	var target := right_button.get_global_rect().get_center()
	touch(target, true)
	await game.get_tree().process_frame
	touch(target, false)
	await game.get_tree().process_frame
	check(game.puzzle.player == Vector2i(2, 2), "Touch should move the player.")
	check(game.metrics.by_level.is_empty(), "Default gameplay must not collect telemetry.")

	game.studio_button.pressed.emit()
	check(game.studio.visible and game.audit.text.contains("41 hamle"), "Workshop should display all routes.")
	game.telemetry.button_pressed = true
	game.zoom.button_pressed = true
	check(game.board.focus_player, "Larger tile setting should reach the board.")
	game.studio_button.pressed.emit()

	var event := InputEventKey.new()
	event.keycode = KEY_RIGHT
	event.pressed = true
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	await game.get_tree().process_frame
	check(game.puzzle.player == Vector2i(3, 2), "Keyboard should move the player.")
	game.actions[&"right"].pressed.emit()
	game.actions[&"right"].pressed.emit()
	check(game.puzzle.player == Vector2i(4, 2) and game.status.text.contains("kapısı kapalı"),
		"Closed gate should block input and explain why.")
	game.actions[&"hint"].pressed.emit()
	check(game.puzzle.player == Vector2i(4, 2) and game.status.text.begins_with("İpucu"),
		"Hint should leave the player's position unchanged.")
	var aggregate: Dictionary = game.metrics.report("synthetic")
	check(aggregate["source"] == "synthetic" and aggregate["levels"]["1"]["blocked"] == 1
		and aggregate["levels"]["1"]["hints"] == 1, "Opt-in aggregate should reflect the exercised inputs.")
	check(aggregate["render_feedback"]["p95_ms"] == null, "Small samples should not produce p95.")
	game.actions[&"undo"].pressed.emit()
	check(game.puzzle.player == Vector2i(3, 2), "Undo should restore the previous tile.")
	game.actions[&"reset"].pressed.emit()
	game.set_telemetry(false)
	game.clear_metrics()
	check(game.metrics.by_level.is_empty(), "Clearing must discard session data.")

	for index in range(Campaign.LEVELS.size()):
		check(game.level == index, "Next should load the expected level.")
		var route: Array = game.puzzle.solution()
		for action in route:
			game.actions[action].pressed.emit()
		check(game.puzzle.won(), "Campaign level should complete with scene controls.")
		if index < Campaign.LEVELS.size() - 1:
			check(not game.level_buttons[index + 1].disabled and game.next.visible,
				"Completing a level should unlock the next.")
			game.next.pressed.emit()
		else:
			check(not game.next.visible and game.status.text.contains("Son sinyal"),
				"Final level should show completion.")
	game.level_buttons[0].pressed.emit()
	check(game.level == 0 and not game.puzzle.won() and game.unlocked == 5,
		"Replay should keep other levels unlocked.")

	var path := "user://verification-progress.cfg"
	var progress := Progress.new(path)
	check(progress.save_unlocked(3) == OK, "Existing four-level progress format should still save.")
	check(Progress.new(path).load_unlocked(6) == 3, "Existing saves should open the original fourth level.")
	check(progress.save_unlocked(5) == OK and Progress.new(path).load_unlocked(6) == 5,
		"New levels should persist locally.")
	DirAccess.remove_absolute(path)
	check(progress.load_unlocked(6) == 0, "Absent save should select the first level.")
