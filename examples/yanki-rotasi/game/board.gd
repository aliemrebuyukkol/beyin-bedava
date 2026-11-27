extends Control

const PANEL := Color("#101e26")
const TRACK := Color("#172a34")
const EDGE := Color("#314751")
const WALL := Color("#0a141a")
const INK := Color("#e5f0ed")
const MINT := Color("#81dbc3")
const AMBER := Color("#f3c175")
const LILAC := Color("#c8aff6")

var puzzle


func _draw() -> void:
	draw_style_box(panel_style(), Rect2(Vector2.ZERO, size))
	if puzzle == null:
		return
	var grid_width: int = puzzle.rows[0].length()
	var grid_height: int = puzzle.rows.size()
	var cell := floorf(minf((size.x - 38.0) / grid_width, (size.y - 38.0) / grid_height))
	var origin := (size - Vector2(grid_width * cell, grid_height * cell)) / 2.0
	for y in range(grid_height):
		for x in range(grid_width):
			var point := Vector2i(x, y)
			var top_left := origin + Vector2(point) * cell + Vector2.ONE * 2
			var bounds := Rect2(top_left, Vector2.ONE * (cell - 4))
			draw_tile(puzzle.tile(point), point, bounds, cell)
	var player_center := origin + (Vector2(puzzle.player) + Vector2(0.5, 0.5)) * cell
	var player_radius := cell * 0.25
	draw_circle(player_center, player_radius + 2, Color("#0a181d"), true, -1, true)
	draw_circle(player_center, player_radius, MINT, true, -1, true)
	draw_circle(player_center, player_radius * 0.40, Color("#153c37"), true, -1, true)


func panel_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = PANEL
	style.border_color = EDGE
	style.set_border_width_all(1)
	style.set_corner_radius_all(22)
	return style


func draw_tile(tile: String, point: Vector2i, bounds: Rect2, cell: float) -> void:
	var middle := bounds.get_center()
	if tile == "#":
		draw_rect(bounds, WALL)
		return
	draw_rect(bounds, TRACK)
	draw_rect(bounds, EDGE, false, 1)
	if tile in ["a", "b", "A", "B"]:
		var accent := AMBER if tile.to_lower() == "a" else LILAC
		if tile == tile.to_upper():
			var opened: bool = puzzle.open_gate(tile, puzzle.echo)
			var bar := Vector2(cell * 0.23, 0)
			var width := 2.0 if opened else 4.0
			var tone := accent.lightened(0.12) if opened else accent
			draw_line(middle - bar + Vector2(0, 7), middle + bar + Vector2(0, 7), tone, width, true)
			center_text(tile + ("·" if opened else "×"), middle - Vector2(0, 6), tone, cell)
		else:
			var active: bool = puzzle.echo == point
			draw_circle(middle, cell * 0.34, accent if active else EDGE, false, 2.0, true)
			if active:
				draw_circle(middle, cell * 0.43, accent, false, 1.0, true)
			center_text(tile.to_upper(), middle, accent, cell)
	elif tile == "E":
		var inset := bounds.grow(-cell * 0.18)
		draw_rect(inset, MINT, false, 2)
		var offset := cell * 0.13
		var tip := middle + Vector2(offset, -offset)
		draw_line(middle + Vector2(-offset, offset), tip, MINT, 2, true)
		draw_line(tip, tip + Vector2(-offset, 0), MINT, 2, true)
		draw_line(tip, tip + Vector2(0, offset), MINT, 2, true)
	else:
		draw_circle(middle, 2.0, EDGE, true, -1, true)


func center_text(value: String, at: Vector2, color: Color, cell: float) -> void:
	var font := get_theme_default_font()
	var font_size := clampi(roundi(cell * 0.34), 11, 24)
	var metrics := font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	draw_string(font, at + Vector2(-metrics.x / 2.0, font_size * 0.34), value,
		HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
