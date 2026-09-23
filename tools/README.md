# Galerie-Vorschaubilder

Nach dem Ergänzen von Bildern in einer `.gallery` aus dem Website-Verzeichnis ausführen:

```sh
python3 tools/optimize-galleries.py
```

Benötigt macOS mit Swift (Apple Command Line Tools). In einem normalen Terminal ausführen: Apples ImageIO benötigt Zugriff auf die lokalen Grafikdienste. Eine eingeschränkte Sandbox kann fehlerhafte Exporte erzeugen.

Das Skript erstellt JPEG-Vorschauen mit bis zu 480, 960 und 1440 Pixel Breite sowie 160-Pixel-Miniaturen in `Bilder/Vorschauen`. Es berücksichtigt die EXIF-Ausrichtung und kontrolliert per SHA-256, dass die Originaldateien unverändert bleiben. Bestehende Vorschauen werden neu erzeugt. Die Ausgabe nennt die gesamte Dateigröße der kleinsten Galerievorschauen, nicht die anfängliche Netzwerkübertragung.

Die ersten zwei Galeriebilder laden sofort, die folgenden über natives Lazy Loading. Der Browser darf Bilder kurz vor dem sichtbaren Bereich vorladen. `srcset` berücksichtigt Darstellungsgröße und Pixeldichte. `gallery.js` verwendet für die Großansicht ausschließlich `data-original`; die Miniaturleiste verwendet `data-thumb`.

Beim Veröffentlichen die geänderten HTML-Dateien, `gallery.js` und den vollständigen Ordner `Bilder/Vorschauen` zusammen übertragen. Die vorhandenen Originalbilder werden weiterhin für die Großansicht benötigt.
