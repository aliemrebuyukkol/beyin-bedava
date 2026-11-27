extends Control

const Puzzle = preload("res://game/puzzle.gd")
const Campaign = preload("res://game/levels.gd")
const Board = preload("res://game/board.gd")
const Progress = preload("res://game/progress.gd")

const INK := Color("#e5f0ed")
const MUTED := Color("#aebfc6")
const MINT := Color("#81dbc3")
const AMBER := Color("#f3c175")
const MINT_INK := Color("#09201d")
const DIRECTIONS := {
	&"up": "yukarı", &"left": "sola", &"down": "aşağı", &"right": "sağa",
}
const KEYS := {
	KEY_UP: &"up", KEY_W: &"up", KEY_LEFT: &"left", KEY_A: &"left",
	KEY_DOWN: &"down", KEY_S: &"down", KEY_RIGHT: &"right", KEY_D: &"right",
	KEY_SPACE: &"echo", KEY_Z: &"undo", KEY_R: &"reset", KEY_H: &"hint",
}

var puzzle
var level := 0
var unlocked := 0
var progress
var can_save := true
var board
var chapter: Label
var title: Label
var brief: Label
var active: Label
var status: Label
var steps: Label
var next: Button
var level_buttons: Array[Button] = []
var actions: Dictionary = {}
var smoke


func _ready() -> void:
	can_save = "--self-test" not in OS.get_cmdline_user_args()
	progress = Progress.new("user://progress.cfg")
	if can_save:
		unlocked = progress.load_unlocked(Campaign.LEVELS.size())
	build_interface()
	open_level(unlocked)
	if not can_save:
		smoke = preload("res://tests/smoke.gd").new()
		smoke.run.call_deferred(self)


func _draw() -> void:
	var canvas := Rect2(Vector2.ZERO, size)
	draw_rect(canvas, Color("#0b151c"))
	draw_rect(Rect2(48, 122, 984, 1), Color("#2d424b"))
	draw_rect(Rect2(48, 643, 984, 1), Color("#2d424b"))


func build_interface() -> void:
	put_label("Yankı Rotası", Rect2(48, 26, 620, 60), 44, INK)
	put_label("Plakaları etkinleştir, sinyal kapılarını aç ve istasyondan çık.",
		Rect2(50, 87, 720, 28), 19, MUTED)
	chapter = put_label("", Rect2(50, 140, 640, 25), 17, MINT)
	steps = put_label("", Rect2(574, 140, 116, 25), 16, MUTED)
	steps.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	board = Board.new()
	board.mouse_filter = Control.MOUSE_FILTER_IGNORE
	place(board, Rect2(48, 174, 644, 405))

	var controls := Panel.new()
	controls.add_theme_stylebox_override("panel", board.panel_style())
	place(controls, Rect2(720, 141, 312, 480))
	title = put_label("", Rect2(742, 162, 268, 36), 28, INK)
	brief = put_label("", Rect2(742, 206, 268, 68), 16, MUTED, true)
	active = put_label("", Rect2(742, 282, 268, 26), 17, MINT)
	status = put_label("", Rect2(742, 312, 268, 66), 17, INK, true)

	action_button(&"up", "Yukarı", Rect2(833, 378, 70, 44), "Yukarı")
	action_button(&"left", "Sol", Rect2(755, 429, 70, 44), "Sol")
	action_button(&"down", "Aşağı", Rect2(833, 429, 70, 44), "Aşağı")
	action_button(&"right", "Sağ", Rect2(911, 429, 70, 44), "Sağ")
	action_button(&"echo", "Yankı bırak  ·  Space", Rect2(742, 486, 268, 48), "Yankı bırak", true)
	action_button(&"undo", "Geri al", Rect2(742, 544, 82, 47), "Geri al  ·  Z")
	action_button(&"hint", "İpucu", Rect2(833, 544, 82, 47), "İpucu  ·  H")
	action_button(&"reset", "Yenile", Rect2(924, 544, 86, 47), "Yenile  ·  R")

	put_label("A / B   Plaka ve kapı     ·     Çerçeveli ok   Çıkış", Rect2(51, 592, 481, 30), 17, MUTED)
	put_label("Bölümler", Rect2(50, 674, 112, 45), 18, INK)
	for index in range(Campaign.LEVELS.size()):
		var button := make_button("%02d" % (index + 1), Rect2(170 + index * 66, 674, 54, 46))
		button.tooltip_text = Campaign.LEVELS[index]["title"]
		button.pressed.connect(open_level.bind(index))
		level_buttons.append(button)
	next = make_button("Sonraki bölüm", Rect2(811, 674, 221, 46), true)
	next.pressed.connect(advance)


func put_label(value: String, bounds: Rect2, font_size: int, color: Color, wrap := false) -> Label:
	var entry := Label.new()
	entry.text = value
	entry.add_theme_font_size_override("font_size", font_size)
	entry.add_theme_color_override("font_color", color)
	if wrap:
		entry.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	entry.mouse_filter = Control.MOUSE_FILTER_IGNORE
	place(entry, bounds)
	return entry


func style(background: Color, frame: Color, border := 1) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = background
	box.border_color = frame
	box.set_border_width_all(border)
	box.set_corner_radius_all(9)
	return box


func make_button(value: String, bounds: Rect2, prominent := false) -> Button:
	var button := Button.new()
	button.text = value
	button.add_theme_font_size_override("font_size", 18)
	var base := MINT if prominent else Color("#172a34")
	var foreground := MINT_INK if prominent else INK
	button.add_theme_color_override("font_color", foreground)
	button.add_theme_color_override("font_hover_color", foreground)
	button.add_theme_color_override("font_pressed_color", foreground)
	button.add_theme_color_override("font_focus_color", foreground)
	button.add_theme_color_override("font_disabled_color", Color("#82949c"))
	button.add_theme_stylebox_override("normal", style(base, Color("#47606a")))
	button.add_theme_stylebox_override("hover", style(base.lightened(0.13), MINT))
	button.add_theme_stylebox_override("pressed", style(base.darkened(0.12), MINT))
	button.add_theme_stylebox_override("disabled", style(Color("#111f27"), Color("#2b3d47")))
	var focus := style(Color(0, 0, 0, 0), AMBER, 2)
	button.add_theme_stylebox_override("focus", focus)
	place(button, bounds)
	return button


func action_button(action: StringName, value: String, bounds: Rect2, accessible_name: String,
		prominent := false) -> void:
	var button := make_button(value, bounds, prominent)
	button.tooltip_text = accessible_name
	button.pressed.connect(act.bind(action))
	actions[action] = button


func place(element: Control, bounds: Rect2) -> void:
	add_child(element)
	element.position = bounds.position
	element.size = bounds.size


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and KEYS.has(event.keycode):
		get_viewport().set_input_as_handled()
		act(KEYS[event.keycode])


func open_level(index: int) -> void:
	if index < 0 or index > unlocked or index >= Campaign.LEVELS.size():
		return
	level = index
	puzzle = Puzzle.new(Campaign.LEVELS[level]["rows"])
	board.puzzle = puzzle
	chapter.text = "Bölüm %02d / %02d" % [level + 1, Campaign.LEVELS.size()]
	title.text = Campaign.LEVELS[level]["title"]
	brief.text = Campaign.LEVELS[level]["brief"]
	show_status("Yön tuşları, WASD veya ekrandaki oklarla ilerle.")
	refresh()


func advance() -> void:
	if puzzle.won() and level + 1 < Campaign.LEVELS.size():
		open_level(level + 1)


func act(action: StringName) -> void:
	if action == &"hint":
		var route: Array = puzzle.solution()
		if puzzle.won():
			show_status("Çıkışa ulaştın.")
		elif route.is_empty():
			show_status("Buradan çıkışa rota yok. Geri al veya bölümü yenile.", AMBER)
		elif route[0] == &"echo":
			show_status("İpucu · Bulunduğun plakaya yankı bırak.", AMBER)
		else:
			show_status("İpucu · Bir adım %s git." % DIRECTIONS[route[0]], AMBER)
		return

	var result: StringName = puzzle.play(action)
	match result:
		&"win":
			unlocked = maxi(unlocked, mini(level + 1, Campaign.LEVELS.size() - 1))
			if can_save and progress.save_unlocked(unlocked) != OK:
				show_status("Çıkış bulundu. İlerleme bu cihazda kaydedilemedi.", AMBER)
			elif level == Campaign.LEVELS.size() - 1:
				show_status("Son sinyal alındı. Dört istasyonu da geçtin!", MINT)
			else:
				show_status("Çıkışı buldun. Sonraki bölüm açıldı.", MINT)
		&"echo":
			show_status("%s hattı etkin. İlgili kapılar açık." % puzzle.active_plate(puzzle.echo).to_upper(), MINT)
		&"plate_required":
			show_status("Yankı bırakmak için A veya B plakasına çık.", AMBER)
		&"already":
			show_status("Yankın zaten bu plakada.", MINT)
		&"gate_a", &"gate_b":
			var letter := "A" if result == &"gate_a" else "B"
			show_status("%s kapısı kapalı. %s plakasına yankı bırak." % [letter, letter], AMBER)
		&"wall":
			show_status("Bu yönde geçit yok.", AMBER)
		&"reset":
			show_status("Bölüm başlangıcına döndün.")
		&"undo":
			show_status("Son hamle geri alındı.")
		&"move":
			var plate: String = puzzle.active_plate(puzzle.player).to_upper()
			show_status("Plaka %s · Yankı bırakmak için Space." % plate if not plate.is_empty() else "")
	refresh()


func show_status(message: String, color := INK) -> void:
	status.text = message
	status.add_theme_color_override("font_color", color)


func refresh() -> void:
	var plate: String = puzzle.active_plate(puzzle.echo)
	active.text = "Etkin hat: %s" % plate.to_upper() if not plate.is_empty() else "Etkin hat: yok"
	steps.text = "%d hamle" % puzzle.history.size()
	next.disabled = not puzzle.won() or level + 1 >= Campaign.LEVELS.size()
	next.visible = puzzle.won() and level + 1 < Campaign.LEVELS.size()
	actions[&"undo"].disabled = puzzle.history.is_empty()
	for index in range(level_buttons.size()):
		var button := level_buttons[index]
		button.disabled = index > unlocked
		button.text = "[%02d]" % (index + 1) if index == level else "%02d" % (index + 1)
	board.queue_redraw()
