extends RefCounted

const LEVELS := [
	{
		"title": "İlk sinyal",
		"brief": "A plakasına git ve yankı bırak. Yankın kapıyı açık tutarken çıkışa yürü.",
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
]
