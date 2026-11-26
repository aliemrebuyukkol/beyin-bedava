# Beyin-Bedava Plugin & Skill

**Beyin-Bedava**, *"Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma"* teknik referansı üzerine kurulu, herhangi bir oyun projesinde komut beklemeden otomatik devreye giren tam kapsamlı oyun etkileşim, para kazanma (reklam & IAP) ve oyuncu koruma mimarisidir.

## Özellikler
- **Komutsuz Otomatik Oyun Keşfi (`rules/AGENTS.md` + `scripts/detect_game_project.py`):** Godot, Unity, Unreal, Phaser/PixiJS/Three.js/Web Canvas, Pygame, Bevy ve LÖVE2D projelerini otomatik tanır; türü belirler, karanlık örüntü risklerini tarar ve `beyin-bedava-config.json` üretir.
- **Algoritmik Çekirdek:** SBMM, EOMM (Çizge Eşleştirme + Markov Karar Süreci), ticari eşleştirme formülü $S(m)$ (`gamma_monetization = 0.0` varsayılanı), DDA (dinamik hitbox `<=1.25x`, mermi manyetizması, hasar çarpanı `<=1.18x`, kritik can $H_{\text{crit}}$ üstel sönümleme).
- **Reklam Yerleşimi (`AdPlacementManager`):** Yalnızca isteğe bağlı ödüllü reklamlar (DDA ile diriltme tuzağı yasak), doğal sınır geçişli ve 2+ ardışık mağlubiyet sonrası otomatik baskılanan ara geçiş reklamları, oyun alanını bozmayan bannerlar ve *Remove Ads* uyumu.
- **Satınalma / IAP Ekranları (`StoreManager` + Store UI):** Gerçek para karşılığı gösterimi, kalıntı tuzağı olmayan paketler, 2 adımlı onay, yayınlanmış oranlar ve sert acıma (*pity*) sayacı, **Restore Purchases** düğmesi, 48 saat soğuma/harcama limiti desteği.
- **Zorunlu Şeffaflık & 5 Katmanlı Dijital Hijyen:** Gri Tonlama (%40 parlaklık sınırı), 20+ sn bilişsel sürtünme, *2-Loss Stop* (30 dk mola), Ekonomik İzolasyon ve Bildirim/Zeigarnik Hijyeni.

---

## Kurulum

### 1. Global Antigravity Eklentisi (Önerilen — Tüm Oyunlarda Otomatik Devreye Girer)
```bash
git clone https://github.com/aliemrebuyukkol/beyin-bedava.git ~/.gemini/config/plugins/beyin-bedava
```

### 2. Tek Bir Oyun Reposuna Taşınabilir Skill Kurulumu
```bash
git clone --depth 1 https://github.com/aliemrebuyukkol/beyin-bedava.git /tmp/beyin-bedava && \
mkdir -p .agents/skills && \
cp -R /tmp/beyin-bedava/skills/beyin-bedava .agents/skills/beyin-bedava && \
rm -rf /tmp/beyin-bedava
```

---

## CLI Araçları

```bash
# 1. Oyun projesini tara ve türe özel beyin-bedava-config.json üret
python3 skills/beyin-bedava/scripts/detect_game_project.py /path/to/game \
  --emit-config /path/to/game/beyin-bedava-config.json

# 2. Stokastik EOMM vs SBMM + DDA sınır simülasyonu çalıştır
python3 skills/beyin-bedava/scripts/simulate_eomm_dda.py --players 1000 --matches 60 --seed 42

# 3. 4 aşamalı telemetri, reklam & mağaza karanlık örüntü denetimi çalıştır
python3 skills/beyin-bedava/scripts/audit_telemetry.py --demo
```

---

## Dizin Yapısı

```text
beyin-bedava/
├── plugin.json
├── README.md
├── LICENSE
├── rules/
│   └── AGENTS.md
└── skills/
    └── beyin-bedava/
        ├── SKILL.md
        ├── references/
        │   ├── ads-and-iap-architecture.md
        │   ├── bibliography.md
        │   ├── genre-and-engine-adapters.md
        │   ├── math-and-algorithms.md
        │   ├── neurobiology-and-economy.md
        │   └── protection-and-audit-protocol.md
        ├── resources/
        │   └── beyin-bedava-config.schema.json
        └── scripts/
            ├── audit_telemetry.py
            ├── detect_game_project.py
            └── simulate_eomm_dda.py
```

## Lisans
[MIT](LICENSE)
