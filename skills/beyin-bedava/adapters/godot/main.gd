extends Control

var charge := 0
var opened := false
var status := Label.new()

func _ready() -> void:
	var panel := VBoxContainer.new()
	panel.position = Vector2(36, 36)
	panel.add_theme_constant_override("separation", 12)
	add_child(panel)
	panel.add_child(status)
	for action in ["Charge", "Pulse", "Reset"]:
		var button := Button.new()
		button.text = action
		button.pressed.connect(play.bind(action))
		panel.add_child(button)
	refresh()
	if "--self-test" in OS.get_cmdline_user_args():
		var buttons := panel.get_children()
		buttons[2].pressed.emit()
		var denied := not opened and charge == 0
		buttons[1].pressed.emit()
		buttons[1].pressed.emit()
		buttons[2].pressed.emit()
		var won := opened and charge == 0 and status.text.contains("Gate open")
		buttons[3].pressed.emit()
		var reset := not opened and charge == 0
		var evidence_ready := emit_evidence({"blocked": denied, "opened": won, "reset": reset})
		if denied and won and reset and evidence_ready:
			print("Pulse Gate: charge, blocked pulse, win and reset verified")
			get_tree().quit()
		else:
			push_error("Pulse Gate smoke test failed")
			get_tree().quit(1)

func play(action: String) -> void:
	if action == "Reset":
		charge = 0
		opened = false
	elif not opened:
		if action == "Charge":
			charge = mini(2, charge + 1)
		elif action == "Pulse" and charge == 2:
			charge = 0
			opened = true
		else:
			status.text = "Pulse needs 2 charges. Try charging first."
			return
	refresh()

func refresh() -> void:
	status.text = "Gate open!" if opened else "Pulse Gate   •   Charge %d / 2" % charge

func emit_evidence(observed: Dictionary) -> bool:
	var plan_path := ""
	var revision := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--evidence-plan="):
			plan_path = argument.trim_prefix("--evidence-plan=")
		elif argument.begins_with("--revision="):
			revision = argument.trim_prefix("--revision=")
	if plan_path.is_empty():
		return revision.is_empty()
	var plan = JSON.parse_string(FileAccess.get_file_as_string(plan_path))
	if not plan is Dictionary or not plan.has("plan_id") or revision.is_empty():
		push_error("Evidence requires a readable integration plan and build revision")
		return false
	print("BEYIN_EVIDENCE " + JSON.stringify({
		"version": 1, "plan_id": plan["plan_id"], "revision": revision,
		"source": "runtime", "checks": [{
			"id": "pulse_flow", "observed": observed, "artifact": "Godot Pulse Gate scene controls"
		}]
	}))
	return true
