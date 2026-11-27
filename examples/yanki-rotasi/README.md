# Yankı Rotası

Beyin-Bedava 2.1.0 ile geliştirilmiş, Türkçe ve dört bölümlük bir Godot bulmacası.

A ve B plakaları aynı harfli kapılara güç verir. Bir plakanın üstündeyken yankı bırak ve kapıdan geç. İkinci bir yankı bıraktığında önceki devre kapanır. Yeşil okla işaretlenen çıkış bir sonraki bölümü açar.

## Çalıştır

```bash
godot --path .
```

Godot 4.7.2 ile doğrulandı. Düzenlemek için Godot Project Manager’da `project.godot` dosyasını içe aktar.

| Kontrol | Tuş |
| --- | --- |
| Hareket | Ok tuşları veya WASD |
| Yankı bırak | Space |
| Geri al | Z |
| Bir sonraki hamle için ipucu | H |
| Bölümü yeniden başlat | R |

Bütün eylemler ekrandaki düğmelerle de yapılabilir. Açılan bölümler cihazda saklanır. Bölüm düğmeleriyle önceki istasyonlara geri dönebilirsin.

## Doğrula

```bash
godot --headless --path . -- --self-test
```

Test gerçek oyun sahnesini çalıştırır. Klavye ve düğme olaylarıyla kapıyı, ipucunu, geri almayı, bölümler arası ilerlemeyi ve yerel kayıt işlevini denetler. Durum uzayını tarayan çözücü, dört bölüm için sırasıyla 9, 15, 23 ve 27 hamlelik en kısa yolları doğrular. Chromium’da fare ve klavyeyle ilk bölüm tamamlandı ve sayfa yenilendiğinde ikinci bölüm geri yüklendi. İnsan playtest’i bekliyor.

`game/puzzle.gd` oyun kurallarını ve çözücüyü, `game/levels.gd` bölüm tasarımlarını, `game/main.gd` ise sahne ve giriş akışını içerir.

## Web dışa aktarma

Godot 4.7.2 dışa aktarma şablonlarını kurduktan sonra hedef klasörü oluştur ve Web preset’ini kullan.

```bash
mkdir -p ../yanki-web
godot --headless --path . --export-release Web ../yanki-web/index.html
cd ../yanki-web
python3 -m http.server 8000 --bind 127.0.0.1
```

Oyunu tarayıcıda `http://127.0.0.1:8000` adresinden aç.
