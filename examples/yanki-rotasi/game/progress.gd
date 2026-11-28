extends RefCounted

var path: String


func _init(save_path: String) -> void:
	path = save_path


func load_unlocked(level_count: int) -> int:
	var file := ConfigFile.new()
	if file.load(path) != OK:
		return 0
	var unlocked: Variant = file.get_value("campaign", "unlocked", 0)
	return clampi(unlocked, 0, level_count - 1) if unlocked is int else 0


func save_unlocked(unlocked: int) -> Error:
	var file := ConfigFile.new()
	file.set_value("campaign", "unlocked", unlocked)
	return file.save(path)
