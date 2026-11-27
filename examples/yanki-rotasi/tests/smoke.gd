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
	var previous_length := 0
	for index in range(Campaign.LEVELS.size()):
		var layout: Array = Campaign.LEVELS[index]["rows"]
		var cells := "".join(layout)
		var width: int = layout[0].length()
		check(cells.count("S") == 1 and cells.count("E") == 1, "Expected one start and exit.")
		for row in layout:
			check(row.length() == width, "Expected rectangular level.")
		var model := Puzzle.new(layout)
		var route := model.solution()
		check(route.size() > previous_length, "Shortest campaign path should grow.")
		var expected_echoes := [1, 1, 2, 3]
		check(route.count(&"echo") == expected_echoes[index], "Unexpected echo sequence.")
		for action in route:
			model.play(action)
		check(model.won(), "Solver route should win.")
		check(model.play(&"undo") == &"undo" and not model.won(), "Undo should recover the pre-win state.")
		model.play(&"reset")
		check(model.player == model.start and model.echo == Puzzle.EMPTY_ECHO, "Reset should clear state.")
		print("Bölüm %d · %d hamle · %d yankı" % [index + 1, route.size(), route.count(&"echo")])
		previous_length = route.size()

	check(game.level == 0 and game.level_buttons[1].disabled, "Level 1 should be initially accessible.")
	game.actions[&"echo"].pressed.emit()
	check(game.status.text.contains("plakasına"), "Echo button should explain how to use a plate.")

	var event := InputEventKey.new()
	event.keycode = KEY_RIGHT
	event.pressed = true
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	await game.get_tree().process_frame
	check(game.puzzle.player == Vector2i(2, 2), "A real key event should move the player.")
	game.actions[&"right"].pressed.emit()
	game.actions[&"right"].pressed.emit()
	game.actions[&"right"].pressed.emit()
	check(game.puzzle.player == Vector2i(4, 2) and game.status.text.contains("kapısı kapalı"),
		"Closed gate should block run-time input and show a readable explanation.")
	game.actions[&"hint"].pressed.emit()
	check(game.puzzle.player == Vector2i(4, 2) and game.status.text.begins_with("İpucu"),
		"Hint should describe an action without advancing the player.")
	game.actions[&"undo"].pressed.emit()
	check(game.puzzle.player == Vector2i(3, 2), "Undo button should restore the previous tile.")
	game.actions[&"reset"].pressed.emit()

	for index in range(Campaign.LEVELS.size()):
		check(game.level == index, "Next should load the expected level.")
		var route: Array = game.puzzle.solution()
		for action in route:
			game.actions[action].pressed.emit()
		check(game.puzzle.won(), "Campaign level should complete with scene controls.")
		if index < Campaign.LEVELS.size() - 1:
			check(not game.level_buttons[index + 1].disabled and game.next.visible,
				"Completing a level should unlock the next level.")
			game.next.pressed.emit()
		else:
			check(not game.next.visible and game.status.text.contains("Son sinyal"),
				"Final level should show campaign completion.")

	game.level_buttons[0].pressed.emit()
	check(game.level == 0 and not game.puzzle.won() and game.unlocked == 3,
		"Replay should allow older levels and preserve unlocks.")

	var path := "user://verification-progress.cfg"
	var progress := Progress.new(path)
	check(progress.save_unlocked(3) == OK, "Progress should write to local storage.")
	check(Progress.new(path).load_unlocked(4) == 3, "Progress should reload from local storage.")
	DirAccess.remove_absolute(path)
	check(progress.load_unlocked(4) == 0, "Absent save should select the first level.")
	if failures == 0:
		print("PASS · campaign, keyboard, controls, hint, undo, reset and progress")
	game.get_tree().quit(int(failures > 0))
