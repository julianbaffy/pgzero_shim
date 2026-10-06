# pgzero_shim – PygameZero-Kompatibilitätslayer für pygbag

[pgzero_shim.py](pgzero_shim.py) bildet eine Teilmenge der PygameZero-API
(`pgzrun`) nach, damit Schülerprojekte fast unverändert mit
[pygbag](https://github.com/pygame-web/pygbag) in den Browser exportiert
werden können. `pgzrun` selbst ist nicht pygbag-kompatibel, da es eine
synchrone Game-Loop nutzt; der Shim treibt stattdessen eine `asyncio`-Loop.

## Verwendung

Statt:

```python
import pgzrun
...
pgzrun.go()
```

schreibt man:

```python
from pgzero_shim import Actor, screen, keyboard, keys, mouse, clock, go
...
go()
```

Die Einstiegsdatei sollte `main.py` heißen (pygbag-Konvention).

## Export mit pygbag

```
pip install pygbag
python3 -m pygbag --build main.py
```

Das erzeugt einen `build/web`-Ordner, der auf einer Website gehostet werden
kann. Zum lokalen Testen gibt `pygbag` eine `http://localhost:8000`-URL aus.


## Umgesetzte Features

### Fenster/Konfiguration
WIDTH, HEIGHT, TITLE:
werden als normale Modul-Variablen im Hauptskript definiert und beim Aufruf von `go()` automatisch ausgelesen.

### Actor
Konstruktor:
`Actor(image, pos=None, **anchor_kwargs)`, z. B. `Actor("alien.png", pos=(50, 50))` oder mit Anker wie `topleft=(0, 0)`.

Positions-/Rect-Attribute:
`x`, `y`, `pos`, `center`, `centerx`, `centery`, `top`, `left`, `bottom`, `right`, `topleft`, `topright`, `bottomleft`, `bottomright`, `midtop`, `midleft`, `midright`, `midbottom`, `width`, `height`, `w`, `h`, `size`.

Bildwechsel:
Zuweisen an `actor.image = "neues_bild.png"` lädt das neue Bild und behält die aktuelle Position bei.

Methoden:
`draw()`, `colliderect(other)` (mit `Actor` oder `pygame.Rect`), `collidepoint(pos)`, `distance_to(target)`, `angle_to(target)`.

Rotation:
`actor.angle` (in Grad, gegen den Uhrzeigersinn) rotiert die Bild-Surface um die Mitte des Actors; bleibt beim Wechsel des `image` erhalten.

### screen
Zeichenmethoden:
`screen.blit(image_oder_surface, pos)`, `screen.fill(color)`, `screen.clear()`.

screen.draw:
`text(text, pos, color, fontname, fontsize)`, `line(start, end, color)`, `rect(rect, color)`, `filled_rect(rect, color)`, `circle(pos, radius, color)`, `filled_circle(pos, radius, color)`.

### Ressourcen-Laden
Bilder:
`images.load(name)` oder per Attribut `images.name` lädt aus dem `images/`-Ordner, mit oder ohne Dateiendung im Namen (`.png`, `.gif`, `.jpg`, `.jpeg` werden automatisch ergänzt); Ergebnisse werden gecacht.

Bild-Eigenschaften:
Geladene Bilder unterstützen `get_width()`, `get_height()`, `get_size()`, `get_rect()` sowie zusätzlich die Attribute `width`, `height`, `size` (wie in der pgzero-Doku, z. B. `images.tree.width`).

Schriftarten:
`fontname` in `screen.draw.text()` wird aus dem `fonts/`-Ordner geladen (`.ttf`/`.otf`), inkl. Cache.

### keyboard und keys
Tastenabfrage:
`keyboard.up`, `keyboard.a`, `keyboard.space` usw. liefern `True`/`False` je nach aktuellem Tastenstatus; `keyboard[keys.SPACE]` funktioniert ebenso.

Tastenkonstanten:
`keys.SPACE`, `keys.UP`, `keys.A` usw. – case-insensitive Lookup über alle `pygame.K_*`-Konstanten.

### mouse
Button-Konstanten:
`mouse.LEFT`, `mouse.MIDDLE`, `mouse.RIGHT`, `mouse.WHEEL_UP`, `mouse.WHEEL_DOWN`.

### clock
Zeitgesteuerte Aufrufe:
`clock.schedule(callback, delay)`, `clock.schedule_unique(callback, delay)`, `clock.schedule_interval(callback, interval)`, `clock.unschedule(callback)` – intern über Delta-Zeit pro Frame statt Threads umgesetzt (browserkompatibel).

### Hooks (im Hauptskript definierbar)
update:
`update(dt)` – wird pro Frame aufgerufen; der Parameter `dt` ist optional angebbar.

draw:
`draw()` – wird pro Frame nach `update()` aufgerufen.

Tastatur-Events:
`on_key_down(key, unicode)`, `on_key_up(key)`.

Maus-Events:
`on_mouse_down(pos, button)`, `on_mouse_up(pos, button)`, `on_mouse_move(pos, rel, buttons)`.

Alle Hook-Parameter sind optional; es werden nur die tatsächlich in der
Funktionssignatur vorhandenen Parameter übergeben (wie bei echtem pgzero).

## Noch nicht umgesetzt

Folgende PygameZero-Features stehen im Shim aktuell nicht zur Verfügung und
müssten bei Bedarf ergänzt werden:

- `sounds` und `music` (inkl. Browser-Autoplay-Einschränkungen)
- `animate()` / `Animation`
- `tone` (Tongenerator)
- `on_music_end()`

