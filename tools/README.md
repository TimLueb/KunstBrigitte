# Galerie-Vorschaubilder

Nach dem Ergänzen von Bildern in einer `.gallery` aus dem Website-Verzeichnis ausführen. Ohne Seitenangabe verarbeitet das Skript alle HTML-Seiten; einzelne Seiten lassen sich gezielt angeben:

```sh
python3 tools/optimize-galleries.py
python3 tools/optimize-galleries.py collagen.html
```

Das Skript berücksichtigt alle `.gallery`-Blöcke jeder ausgewählten Seite.

Benötigt `ffmpeg` und `ffprobe` im `PATH`. Die Vorschauen werden mit FFmpeg auf der CPU erzeugt, nicht über Apples ImageIO.

Das Skript erstellt JPEG-Vorschauen mit bis zu 480, 960 und 1440 Pixel Breite sowie 160-Pixel-Miniaturen in `Bilder/Vorschauen`. Es berücksichtigt die Bildausrichtung, prüft die decodierbaren Bildmaße und vergleicht kleine Helligkeitsproben mit dem Original, damit schwarze oder stark abgedunkelte Exporte nicht übernommen werden. Alle Vorschauen werden zunächst temporär neben dem Ziel erzeugt und geprüft; erst danach ersetzen sie die vorhandenen Dateien atomar. SHA-256 stellt sicher, dass die Originaldateien unverändert bleiben. Die Ausgabe nennt die gesamte Dateigröße der kleinsten Galerievorschauen, nicht die anfängliche Netzwerkübertragung.

Die ersten zwei Galeriebilder laden sofort, die folgenden über natives Lazy Loading. Der Browser darf Bilder kurz vor dem sichtbaren Bereich vorladen. `srcset` berücksichtigt Darstellungsgröße und Pixeldichte. `gallery.js` verwendet für die Großansicht ausschließlich `data-original`; die Miniaturleiste verwendet `data-thumb`.

Beim Veröffentlichen die geänderten HTML-Dateien, `gallery.js` und den vollständigen Ordner `Bilder/Vorschauen` zusammen übertragen. Die vorhandenen Originalbilder werden weiterhin für die Großansicht benötigt.
