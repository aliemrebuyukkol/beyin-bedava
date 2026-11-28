extends RefCounted

const LEVELS := [
	{
		"title": "İlk sinyal",
		"brief": "A plakasına yankı bırak ve açık kapıdan çıkışa git.",
		"rows": [
			"#########",
			"###.a####",
			"#S...A.E#",
			"#########",
		],
	},
	{
		"title": "Yan hat",
		"brief": "A plakasına alt koridordan ulaş. Yankı çalışırken ana hatta geri dön.",
		"rows": [
			"###########",
			"#S....A..E#",
			"#.##.######",
			"#....a....#",
			"###########",
		],
	},
	{
		"title": "Devre değişimi",
		"brief": "A kapısından geçtikten sonra yankını B plakasına taşı. Bir anda tek yankın olabilir.",
		"rows": [
			"############",
			"#S..A...B.E#",
			"#.#.#.######",
			"#a..#..b...#",
			"############",
		],
	},
	{
		"title": "Son istasyon",
		"brief": "A ve B hatlarını sırayla kullan. Son geçit ilk yankının yeniden etkinleşmesini gerektirir.",
		"rows": [
			"###############",
			"#S...A...B..AE#",
			"#.##.###.##..##",
			"#a...###b###a##",
			"###############",
		],
	},
	{
		"title": "Tek yön",
		"brief": "Ok işaretli geçide soldan gir. B plakasında yankı bırak ve koridoru takip et.",
		"rows": [
			"##############",
			"#S..>......BE#",
			"#.##.####.####",
			"#....#.......#",
			"############.#",
			"#########b...#",
			"##############",
		],
	},
	{
		"title": "Yedek güç",
		"brief": "A hattını aç. B kapısını geçmeden önce güç hücresini bul ve X kapısına güç ver.",
		"rows": [
			"################",
			"#S...A...B...XE#",
			"#.##.###.#######",
			"#a...###b......#",
			"##############.#",
			"#############k.#",
			"################",
		],
	},
]
