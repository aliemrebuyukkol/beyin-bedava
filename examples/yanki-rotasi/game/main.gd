extends Control

const Puzzle = preload("res://game/puzzle.gd")
const Campaign = preload("res://game/levels.gd")
const Board = preload("res://game/board.gd")
const Progress = preload("res://game/progress.gd")
const Metrics = preload("res://game/metrics.gd")

const INK := Color("#e5f0ed")
const MUTED := Color("#aebfc6")
const MINT := Color("#81dbc3")
const AMBER := Color("#f3c175")
const MINT_INK := Color("#09201d")
const DIRECTIONS := {&"up": "yukarı", &"left": "sola", &"down": "aşağı", &"right": "sağa"}
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
var metrics := Metrics.new()
var smoke

var scroll: ScrollContainer
var edge: MarginContainer
var surface: VBoxContainer
var columns: BoxContainer
var play_page: VBoxContainer
var studio: VBoxContainer
var studio_button: Button
var board: Control
var chapter: Label
var title: Label
var brief: Label
var active: Label
var status: Label
var steps: Label
var next: Button
var telemetry: CheckButton
var zoom: CheckButton
var stats: Label
var audit: Label
var export_button: Button
var export_status: Label
var level_buttons: Array[Button] = []
var actions: Dictionary = {}


func _ready() -> void:
	get_window().min_size = Vector2i(320, 320)
	if OS.has_feature("web"):
		get_window().content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		get_window().content_scale_size = Vector2i.ZERO
		get_window().content_scale_factor = float(JavaScriptBridge.eval("window.devicePixelRatio || 1", true))
	can_save = "--self-test" not in OS.get_cmdline_user_args() and "--audit" not in OS.get_cmdline_user_args()
	progress = Progress.new("user://progress.cfg")
	if can_save:
		unlocked = progress.load_unlocked(Campaign.LEVELS.size())
	build_interface()
	resized.connect(layout)
	layout()
	open_level(unlocked)
	RenderingServer.frame_post_draw.connect(metrics.frame_drawn)
	if not can_save:
		smoke = preload("res://tests/smoke.gd").new()
		smoke.run.call_deferred(self)


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color("#0b151c"))


func layout() -> void:
	var wide := size.x >= 650
	var inset := maxi(10, roundi((size.x - 1070.0) / 2.0)) if wide else 10
	edge.add_theme_constant_override("margin_left", inset)
	edge.add_theme_constant_override("margin_right", inset)
	columns.vertical = not wide
	columns.add_theme_constant_override("separation", 18 if wide else 8)
	board.custom_minimum_size = Vector2(0, clampf(size.y * 0.54, 176.0, 420.0) if wide
		else clampf(size.x * (0.46 if size.y < 650 else 0.52), 140.0, 235.0))
	queue_redraw()


func build_interface() -> void:
	scroll = ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus = true
	add_child(scroll)
	scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	edge = MarginContainer.new()
	edge.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	edge.add_theme_constant_override("margin_top", 10)
	edge.add_theme_constant_override("margin_bottom", 14)
	scroll.add_child(edge)
	surface = VBoxContainer.new()
	edge.add_child(surface)
	surface.add_theme_constant_override("separation", 8)

	var header := row(surface)
	var heading := label(header, "Yankı Rotası", 27, INK)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	studio_button = button(header, "Atölye")
	studio_button.custom_minimum_size.x = 90
	studio_button.pressed.connect(toggle_studio)

	play_page = column(surface, 8)
	columns = BoxContainer.new()
	play_page.add_child(columns)
	var stage := column(columns, 6)
	stage.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stage.size_flags_stretch_ratio = 1.38
	var stage_header := row(stage)
	chapter = label(stage_header, "", 16, MINT)
	chapter.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	steps = label(stage_header, "", 15, MUTED)
	board = Board.new()
	board.clip_contents = true
	board.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stage.add_child(board)
	label(stage, "Harfler kapıları, ok çıkışı gösterir", 14, MUTED, true)

	var controls := column(columns, 5)
	controls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title = label(controls, "", 22, INK)
	brief = label(controls, "", 15, MUTED, true)
	active = label(controls, "", 15, MINT)
	status = label(controls, "", 15, INK, true)
	status.custom_minimum_size.y = 40

	var arrows := row(controls)
	action_button(arrows, &"left", "Sol", "Sol")
	action_button(arrows, &"up", "Yukarı", "Yukarı")
	action_button(arrows, &"down", "Aşağı", "Aşağı")
	action_button(arrows, &"right", "Sağ", "Sağ")
	var primary := row(controls)
	action_button(primary, &"echo", "Yankı bırak", "Yankı bırak · Space", true)
	next = button(primary, "Sonraki bölüm", true)
	next.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	next.pressed.connect(advance)

	var utilities := row(controls)
	action_button(utilities, &"undo", "Geri al", "Geri al · Z")
	action_button(utilities, &"hint", "İpucu", "İpucu · H")
	action_button(utilities, &"reset", "Yenile", "Yenile · R")

	label(play_page, "Bölümler", 15, INK)
	var levels := row(play_page)
	for index in range(Campaign.LEVELS.size()):
		var control := button(levels, "%02d" % (index + 1))
		control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		control.tooltip_text = Campaign.LEVELS[index]["title"]
		control.pressed.connect(select_level.bind(index))
		level_buttons.append(control)

	studio = column(surface, 10)
	studio.visible = false
	label(studio, "Oyun atölyesi", 26, MINT)
	label(studio, "Bölüm denetimi ve isteğe bağlı oturum ölçümü", 16, MUTED, true)
	zoom = CheckButton.new()
	zoom.text = "Büyük kareler"
	zoom.custom_minimum_size.y = 48
	studio.add_child(zoom)
	zoom.toggled.connect(set_zoom)
	telemetry = CheckButton.new()
	telemetry.text = "Bu oturumun ölçümünü aç"
	telemetry.custom_minimum_size.y = 48
	studio.add_child(telemetry)
	telemetry.toggled.connect(set_telemetry)
	label(studio, "Sayaçlar cihazında kalır. JSON dosyasını yalnızca sen dışa aktarırsın.", 15, MUTED, true)
	stats = label(studio, "", 16, INK, true)
	var telemetry_actions := row(studio)
	export_button = button(telemetry_actions, "JSON dışa aktar")
	export_button.disabled = true
	export_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	export_button.pressed.connect(export_metrics)
	var clear_button := button(telemetry_actions, "Temizle")
	clear_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	clear_button.pressed.connect(clear_metrics)
	export_status = label(studio, "", 15, MINT, true)
	label(studio, "Bölüm denetimi", 20, MINT)
	audit = label(studio, "", 16, INK, true)
	label(studio, "Hamleler çözücünün en kısa rotalarıdır. Oyuncu deneyimi için ayrı playtest gerekir.",
		15, MUTED, true)


func row(parent: Control) -> HBoxContainer:
	var box := HBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	parent.add_child(box)
	return box


func column(parent: Control, separation: int) -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", separation)
	parent.add_child(box)
	return box


func label(parent: Control, value: String, font_size: int, color: Color, wrap := false) -> Label:
	var entry := Label.new()
	entry.text = value
	entry.add_theme_font_size_override("font_size", font_size)
	entry.add_theme_color_override("font_color", color)
	if wrap:
		entry.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	entry.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(entry)
	return entry


func style(background: Color, frame: Color, border := 1) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = background
	box.border_color = frame
	box.set_border_width_all(border)
	box.set_corner_radius_all(9)
	return box


func button(parent: Control, value: String, prominent := false) -> Button:
	var control := Button.new()
	control.text = value
	control.custom_minimum_size = Vector2(44, 50)
	control.add_theme_font_size_override("font_size", 16)
	var base := MINT if prominent else Color("#172a34")
	var ink := MINT_INK if prominent else INK
	for name in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		control.add_theme_color_override(name, ink)
	control.add_theme_color_override("font_disabled_color", Color("#82949c"))
	control.add_theme_stylebox_override("normal", style(base, Color("#47606a")))
	control.add_theme_stylebox_override("hover", style(base.lightened(0.13), MINT))
	control.add_theme_stylebox_override("pressed", style(base.darkened(0.12), MINT))
	control.add_theme_stylebox_override("disabled", style(Color("#111f27"), Color("#2b3d47")))
	control.add_theme_stylebox_override("focus", style(Color(0, 0, 0, 0), AMBER, 2))
	parent.add_child(control)
	return control


func action_button(parent: Control, action: StringName, value: String, tooltip: String,
		prominent := false) -> void:
	var control := button(parent, value, prominent)
	control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	control.tooltip_text = tooltip
	control.pressed.connect(act.bind(action))
	actions[action] = control


func _input(event: InputEvent) -> void:
	if puzzle != null and play_page.visible and event is InputEventKey and event.pressed \
			and not event.echo and KEYS.has(event.keycode):
		get_viewport().set_input_as_handled()
		act(KEYS[event.keycode])


func select_level(index: int) -> void:
	if index != level:
		open_level(index)


func open_level(index: int) -> void:
	if index < 0 or index > unlocked or index >= Campaign.LEVELS.size():
		return
	level = index
	puzzle = Puzzle.new(Campaign.LEVELS[level]["rows"])
	board.puzzle = puzzle
	chapter.text = "Bölüm %02d / %02d" % [level + 1, Campaign.LEVELS.size()]
	title.text = Campaign.LEVELS[level]["title"]
	brief.text = Campaign.LEVELS[level]["brief"]
	show_status("Ekrandaki yön tuşlarıyla ilerle.")
	refresh()
	scroll.set_deferred("scroll_vertical", 0)


func advance() -> void:
	if puzzle.won() and level + 1 < Campaign.LEVELS.size():
		open_level(level + 1)


func act(action: StringName) -> void:
	var started := Time.get_ticks_usec()
	if action == &"hint":
		show_hint()
		metrics.record(level, action, &"hint", started)
		return
	var result: StringName = puzzle.play(action)
	metrics.record(level, action, result, started)
	match result:
		&"win":
			unlocked = maxi(unlocked, mini(level + 1, Campaign.LEVELS.size() - 1))
			if can_save and progress.save_unlocked(unlocked) != OK:
				show_status("Çıkış bulundu. İlerleme bu cihazda kaydedilemedi.", AMBER)
			elif level == Campaign.LEVELS.size() - 1:
				show_status("Son sinyal alındı. Altı istasyonu da geçtin!", MINT)
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
		&"one_way":
			show_status("Tek yönlü geçide yalnızca soldan girilir.", AMBER)
		&"needs_power":
			show_status("X kapısı için güç hücresini bul.", AMBER)
		&"power":
			show_status("Güç hücresi alındı. X kapısı hazır.", MINT)
		&"reset":
			show_status("Bölüm başlangıcına döndün.")
		&"undo":
			show_status("Son hamle geri alındı.")
		&"move":
			var plate: String = puzzle.active_plate(puzzle.player).to_upper()
			show_status("Plaka %s · Yankı bırakabilirsin." % plate if not plate.is_empty() else "")
	refresh()


func show_hint() -> void:
	var route: Array = puzzle.solution()
	if puzzle.won():
		show_status("Çıkışa ulaştın.")
	elif route.is_empty():
		show_status("Buradan çıkışa rota yok. Geri al veya bölümü yenile.", AMBER)
	elif route[0] == &"echo":
		show_status("İpucu · Bulunduğun plakaya yankı bırak.", AMBER)
	else:
		show_status("İpucu · Bir adım %s git." % DIRECTIONS[route[0]], AMBER)


func show_status(message: String, color := INK) -> void:
	status.text = message
	status.add_theme_color_override("font_color", color)


func refresh() -> void:
	var plate: String = puzzle.active_plate(puzzle.echo).to_upper()
	active.text = "Etkin hat: %s%s" % [plate if not plate.is_empty() else "yok",
		" · Güç var" if puzzle.battery else ""]
	steps.text = "%d hamle" % puzzle.history.size()
	next.visible = puzzle.won() and level + 1 < Campaign.LEVELS.size()
	actions[&"undo"].disabled = puzzle.history.is_empty()
	for index in range(level_buttons.size()):
		var control := level_buttons[index]
		control.disabled = index > unlocked
		control.text = "[%02d]" % (index + 1) if index == level else "%02d" % (index + 1)
	board.queue_redraw()


func toggle_studio() -> void:
	studio.visible = not studio.visible
	play_page.visible = not studio.visible
	studio_button.text = "Oyuna dön" if studio.visible else "Atölye"
	scroll.set_deferred("scroll_vertical", 0)
	if studio.visible:
		var lines: PackedStringArray = []
		for index in range(Campaign.LEVELS.size()):
			var demo := Puzzle.new(Campaign.LEVELS[index]["rows"])
			var route := demo.solution()
			var result := "%d hamle" % route.size() if not route.is_empty() else "Rota bulunamadı"
			lines.append("%02d · %s — %s" % [index + 1, Campaign.LEVELS[index]["title"], result])
		audit.text = "\n".join(lines)
		refresh_studio()


func set_zoom(value: bool) -> void:
	board.focus_player = value
	board.queue_redraw()


func set_telemetry(value: bool) -> void:
	metrics.set_enabled(value)
	refresh_studio()


func clear_metrics() -> void:
	metrics.clear()
	export_status.text = "Oturum ölçümleri temizlendi."
	refresh_studio()


func refresh_studio() -> void:
	var moves := 0
	var hints := 0
	var blocked := 0
	for item in metrics.by_level.values():
		moves += item["actions"]
		hints += item["hints"]
		blocked += item["blocked"]
	var latency = metrics.p95()
	stats.text = "Eylem %d · Engellenen %d · İpucu %d\nÇizim ölçümü %d örnek · %s" % [
		moves, blocked, hints, metrics.frame_ms.size(),
		"p95 %.1f ms" % latency if latency != null else "p95 için en az 30 örnek gerekli"]
	export_button.disabled = metrics.by_level.is_empty()


func export_metrics() -> void:
	var payload := JSON.stringify(metrics.report(), "\t")
	if OS.has_feature("web"):
		JavaScriptBridge.download_buffer(payload.to_utf8_buffer(), "yanki-oturumu.json", "application/json")
		export_status.text = "JSON tarayıcıya gönderildi."
	else:
		var file := FileAccess.open("user://yanki-oturumu.json", FileAccess.WRITE)
		if file == null:
			export_status.text = "JSON bu cihazda kaydedilemedi."
			return
		file.store_string(payload)
		file.close()
		export_status.text = "JSON kaydedildi: " + ProjectSettings.globalize_path("user://yanki-oturumu.json")
