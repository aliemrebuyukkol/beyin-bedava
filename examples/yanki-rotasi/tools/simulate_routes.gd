extends SceneTree
## Compare two scripted navigation policies on the actual level rules.
## Run with godot --headless --path . --script res://tools/simulate_routes.gd.

const Puzzle = preload("res://game/puzzle.gd")
const Campaign = preload("res://game/levels.gd")
const TRIALS := 24
const ACTION_LIMIT := 96
const FIRST_SEED := 4200


func _initialize() -> void:
	var results := []
	for index in range(Campaign.LEVELS.size()):
		var rows: Array = Campaign.LEVELS[index]["rows"]
		var random_wins := 0
		var guide_wins := 0
		for seed in range(FIRST_SEED, FIRST_SEED + TRIALS):
			random_wins += int(play(rows, seed, false))
			guide_wins += int(play(rows, seed, true))
		results.append({"level": index + 1, "random_solved": random_wins, "guided_solved": guide_wins})
	print(JSON.stringify({
		"source": "synthetic",
		"trials_per_level_and_policy": TRIALS,
		"first_seed": FIRST_SEED,
		"action_limit": ACTION_LIMIT,
		"random_policy": "Uniform selection among state-changing actions.",
		"guided_policy": "Follow shortest solution on every second action when available.",
		"results": results,
	}, "\t"))
	quit()


func play(rows: Array, seed: int, guided: bool) -> bool:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var model := Puzzle.new(rows)
	var actions: Array = Puzzle.ACTIONS.keys()
	actions.append(&"echo")
	for index in range(ACTION_LIMIT):
		var current := model.snapshot()
		var choices: Array[StringName] = []
		for action in actions:
			if model.transition(current, action) != current:
				choices.append(action)
		if choices.is_empty():
			break
		var next_action := choices[rng.randi_range(0, choices.size() - 1)]
		if guided and index % 2 == 1:
			var route := model.solution()
			if not route.is_empty():
				next_action = route[0]
		model.play(next_action)
		if model.won():
			return true
	return false
