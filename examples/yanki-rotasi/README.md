# Yankı Rotası

Beyin-Bedava 2.1.0 ile geliştirilmiş, Türkçe ve altı bölümlük bir Godot bulmacası. Dikey telefonda oyun alanı kontrollerin üstünde, geniş ve yatay ekranda ise yanında durur.

A ve B plakaları aynı harfli kapılara güç verir. Yeni bir yankı bırakınca önceki devre kapanır. 5. bölüm tek yönlü geçitleri, 6. bölüm güç hücresini ve X kapısını ekler. Çerçeveli ok bir sonraki bölümü açan çıkışı gösterir.

## Oyna

[Tarayıcıda oyna](https://yanki-rotasi.kafamdakisey.chatgpt.site) · ChatGPT hesabı gerekir. Godot 4.7.2’de `project.godot` dosyasını açıp **F5** ile de çalıştırabilirsin.

| Ekrandaki düğme | Klavye |
| --- | --- |
| Yön tuşları | Ok tuşları / WASD |
| Yankı bırak | Space |
| Geri al | Z |
| İpucu | H |
| Yenile | R |

Oyun açılan bölümleri cihazda tutar. **Atölye** bölümünde büyük karelere geçebilir, en kısa çözüm uzunluklarını görebilir ve isteğe bağlı oturum ölçümünü açabilirsin. Ölçümü açarsan sayaçlar yalnızca bellekte tutulur. **JSON dışa aktar** seçtiğinde cihazına bir dosya yazılır. **Temizle** oturumu siler.

## Skill’in kullanımı

| Yetenek | Bu örnekte uygulama |
| --- | --- |
| Mekanik ve oyun hissi | Tek yankı, tek yönlü geçit, güç hücresi, görünür geri bildirim, dokunmatik ve klavye kontrolleri |
| Seviye ve ilerleme denetimi | Oyunla aynı geçiş fonksiyonunu kullanan çözücü. Altı rota, dört mekanik birleşimi, artan hamle uzunlukları ve tekrar denetimi. [Denetim sonucu](qa/level-audit.json) |
| Görev ve dosya sahipliği | Önce kurallar, sonra mobil arayüz, sonra doğrulama. SQLite defteri checkpoint ve önizleme kesintisinden devamı kaydetti. [Görev kanıtı](qa/task-ledger-summary.json) |
| Sentetik simülasyon | Aynı kurallarda 24 eşleştirilmiş tohumla rastgele ve ipucu kullanan sentetik gezginlerin karşılaştırması. [Simülasyon kanıtı](qa/simulation.json) |
| Telemetri | Yerel eylem, engellenme ve ipucu sayaçları. Godot giriş callback’i ile çizim sinyali arasındaki süre, oturumda yeterli örnek varsa p95 olarak gösterilir. JSON doğrulayıcısı eksik örneklemi, imkânsız sayaçları ve tutarsız yüzdelikleri işaretler. [Sentetik test verisi](qa/synthetic-session.json) |
| Oyuncu deneyimi | Anlamlı seçim, hedeflenen duygu ve çizim gecikmesi için [ölçüm planı](qa/experience-plan.json). İnsan playtest’i bekliyor. |
| Skill açık/kapalı benchmark | Yankı Rotası’nın geçiş kuralı için 144 kabul girdisi ve iki yerel Qwen çifti. İki koşul da kuralları doğru çözemedi. Yaratıcılık göstergesi %0’dan %50’ye, ortalama toplam token 514,5’ten 2.281,5’e çıktı. [Ham sonuç](qa/benchmark.json) |

Godot proje tanıma, Tasarım Vergisi görev paylaşımı, sentetik denge simülasyonu ve diğer motor veya host adaptörleri için Beyin-Bedava’nın [2.1.0 geliştirme dalındaki araçları](https://github.com/aliemrebuyukkol/beyin-bedava/tree/release/beyin-bedava-2.1.0) kullanılır. Bu bulmaca Godot ile çalışır.

## Doğrula

```bash
godot --headless --path . -- --self-test
godot --headless --path . -- --audit
godot --headless --path . --script res://tools/simulate_routes.gd
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/check_session.py qa/synthetic-session.json
```

Godot testi altı bölümün çözümünü, dokunmayı, klavyeyi, ipucunu, geri almayı, ölçüm iznini ve eski kayıtların açılmasını denetler. Düzen Godot ve Chromium’da 320 × 568, 390 × 844, 844 × 390 ve 1080 × 760 boyutlarında doğrulandı. Chromium telefon emülasyonunda ilk bölüm dokunarak tamamlandı ve Atölye’den indirilen dokuz eylemlik JSON doğrulandı. Fiziksel telefon testi bekliyor.

2.1.0 kaynak ağacı ve OpenAI uyumlu yerel model uç noktasıyla örnek benchmark’ı yeniden çalıştırabilirsin.

```bash
python3 tools/bench_gate.py --beyin-repo /path/to/beyin-bedava-2.1 \
  --endpoint http://127.0.0.1:4187/v1/chat/completions \
  --model qwen2.5-coder-1.5b-instruct-q4-k-m --output /tmp/yanki-benchmark.json
```

## Web dışa aktarma

Godot 4.7.2 dışa aktarma şablonları kuruluysa Web preset’ini kullan.

```bash
mkdir -p ../yanki-web
godot --headless --path . --export-release Web ../yanki-web/index.html
cd ../yanki-web
python3 -m http.server 8000 --bind 127.0.0.1
```

Tarayıcıda `http://127.0.0.1:8000` adresini aç.
