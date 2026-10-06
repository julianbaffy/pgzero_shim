"""Pygbag-kompatibler Ersatz für pgzrun.

Bildet nur die tatsächlich in den Unterrichtsspielen genutzte PygameZero-API
nach (Actor, screen, keyboard, keys, clock, Hooks update/draw/on_key_down/...).
pgzrun selbst laesst sich nicht mit pygbag exportieren, da es eine synchrone
Game-Loop nutzt; dieser Shim treibt stattdessen eine asyncio-Loop, wie sie
pygbag im Browser benoetigt.
"""
import asyncio
import inspect
import math
import os

import pygame

pygame.init()
# Ein frueher (Platzhalter-)Displaymodus wird benoetigt, damit convert_alpha()
# beim Laden von Bildern auf Modulebene (vor go()) funktioniert.
pygame.display.set_mode((1, 1))

WIDTH = 600
HEIGHT = 600
TITLE = "PygameZero"

_RECT_ATTRS = {
    "top", "left", "bottom", "right", "centerx", "centery",
    "topleft", "bottomleft", "topright", "bottomright",
    "midtop", "midleft", "midright", "midbottom", "center",
    "width", "height", "w", "h", "size",
}
# pgzero verankert x/y standardmaessig an der Mitte, nicht an rect.x/rect.left.
_ALIASES = {"pos": "center", "x": "centerx", "y": "centery"}


class _ImageSurface(pygame.Surface):
    """Wie pygame.Surface, ergaenzt um pgzero-typische width/height/size-Attribute."""

    @property
    def width(self):
        return self.get_width()

    @property
    def height(self):
        return self.get_height()

    @property
    def size(self):
        return self.get_size()


class _Images:
    def __init__(self):
        self._cache = {}

    def __getattr__(self, name):
        return self.load(name)

    def load(self, name):
        if isinstance(name, pygame.Surface):
            return name
        if name in self._cache:
            return self._cache[name]
        base, ext = os.path.splitext(name)
        candidates = [name] if ext else [name + e for e in (".png", ".gif", ".jpg", ".jpeg")]
        for candidate in candidates:
            path = os.path.join("images", candidate)
            if os.path.exists(path):
                raw = pygame.image.load(path)
                surface = _ImageSurface(raw.get_size(), pygame.SRCALPHA)
                surface.blit(raw, (0, 0))
                surface = surface.convert_alpha()
                self._cache[name] = surface
                return surface
        raise FileNotFoundError(f"Bild nicht gefunden: {name}")


images = _Images()


class _Fonts:
    def __init__(self):
        self._cache = {}

    def load(self, fontname, size):
        key = (fontname, size)
        if key in self._cache:
            return self._cache[key]
        if fontname:
            path = os.path.join("fonts", fontname)
            if not os.path.exists(path):
                for ext in (".ttf", ".otf"):
                    if os.path.exists(path + ext):
                        path = path + ext
                        break
            font = pygame.font.Font(path, size)
        else:
            font = pygame.font.Font(None, size)
        self._cache[key] = font
        return font


_fonts = _Fonts()


class Actor:
    def __init__(self, image, pos=None, **anchor_kwargs):
        object.__setattr__(self, "image", image)
        object.__setattr__(self, "_angle", 0)
        surface = images.load(image)
        object.__setattr__(self, "_base_surf", surface)
        object.__setattr__(self, "_surf", surface)
        rect = surface.get_rect()
        object.__setattr__(self, "_rect", rect)
        if pos is not None:
            rect.center = pos
        for name, value in anchor_kwargs.items():
            setattr(rect, _ALIASES.get(name, name), value)

    def __getattr__(self, name):
        if name == "angle":
            return self._angle
        real = _ALIASES.get(name, name)
        if real in _RECT_ATTRS:
            return getattr(self._rect, real)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == "image":
            object.__setattr__(self, "image", value)
            object.__setattr__(self, "_base_surf", images.load(value))
            self._apply_rotation(self._rect.center)
            return
        if name == "angle":
            object.__setattr__(self, "_angle", value % 360)
            self._apply_rotation(self._rect.center)
            return
        real = _ALIASES.get(name, name)
        if real in _RECT_ATTRS:
            setattr(self._rect, real, value)
        else:
            object.__setattr__(self, name, value)

    def _apply_rotation(self, center):
        rotated = pygame.transform.rotate(self._base_surf, self._angle) if self._angle else self._base_surf
        object.__setattr__(self, "_surf", rotated)
        object.__setattr__(self, "_rect", rotated.get_rect())
        self._rect.center = center

    def draw(self):
        screen.surface.blit(self._surf, self._rect)

    def colliderect(self, other):
        rect = other._rect if isinstance(other, Actor) else other
        return self._rect.colliderect(rect)

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)

    def distance_to(self, target):
        tx, ty = target.pos if isinstance(target, Actor) else target
        return math.hypot(tx - self.x, ty - self.y)

    def angle_to(self, target):
        tx, ty = target.pos if isinstance(target, Actor) else target
        return math.degrees(math.atan2(self.y - ty, tx - self.x))


class _Draw:
    def __init__(self, surface):
        self.surface = surface

    def text(self, text, pos=(0, 0), color=(255, 255, 255), fontname=None, fontsize=24, **kwargs):
        font = _fonts.load(fontname, fontsize)
        image = font.render(text, True, color)
        self.surface.blit(image, pos)

    def line(self, start, end, color):
        pygame.draw.line(self.surface, color, start, end)

    def rect(self, rect, color):
        pygame.draw.rect(self.surface, color, rect, width=1)

    def filled_rect(self, rect, color):
        pygame.draw.rect(self.surface, color, rect)

    def circle(self, pos, radius, color):
        pygame.draw.circle(self.surface, color, pos, radius, width=1)

    def filled_circle(self, pos, radius, color):
        pygame.draw.circle(self.surface, color, pos, radius)


class Screen:
    def __init__(self, surface):
        self.surface = surface
        self.draw = _Draw(surface)

    def blit(self, image, pos):
        surface = images.load(image) if isinstance(image, str) else image
        self.surface.blit(surface, pos)

    def fill(self, color):
        self.surface.fill(color)

    def clear(self):
        self.surface.fill((0, 0, 0))


screen = Screen(pygame.Surface((1, 1)))


# pygame-Tastenkonstanten sind uneinheitlich benannt (K_UP, aber K_a), daher
# einmalig eine Lowercase-Lookup-Tabelle aufbauen statt "K_" + name.lower().
_KEY_CONSTANTS = {
    name[2:].lower(): value
    for name, value in vars(pygame).items()
    if name.startswith("K_")
}


class _Keyboard:
    def __getattr__(self, name):
        const = _KEY_CONSTANTS.get(name.lower())
        if const is None:
            raise AttributeError(name)
        return bool(pygame.key.get_pressed()[const])

    def __getitem__(self, key_const):
        return bool(pygame.key.get_pressed()[key_const])


keyboard = _Keyboard()


class _Keys:
    def __getattr__(self, name):
        const = _KEY_CONSTANTS.get(name.lower())
        if const is None:
            raise AttributeError(name)
        return const


keys = _Keys()


class _Mouse:
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    WHEEL_UP = 4
    WHEEL_DOWN = 5


mouse = _Mouse()


class _Clock:
    def __init__(self):
        self._events = []

    def schedule(self, callback, delay):
        self._events.append({"cb": callback, "interval": None, "remaining": delay})

    def schedule_unique(self, callback, delay):
        self.unschedule(callback)
        self.schedule(callback, delay)

    def schedule_interval(self, callback, interval):
        self._events.append({"cb": callback, "interval": interval, "remaining": interval})

    def unschedule(self, callback):
        self._events = [e for e in self._events if e["cb"] != callback]

    def tick(self, dt):
        due = []
        for event in self._events:
            event["remaining"] -= dt
            if event["remaining"] <= 0:
                due.append(event)
        for event in due:
            if event["interval"] is not None:
                event["remaining"] += event["interval"]
            else:
                self._events.remove(event)
            event["cb"]()


clock = _Clock()


def _call_hook(fn, **kwargs):
    params = inspect.signature(fn).parameters
    args = {k: v for k, v in kwargs.items() if k in params}
    fn(**args)


async def _run(module_globals):
    width = module_globals.get("WIDTH", WIDTH)
    height = module_globals.get("HEIGHT", HEIGHT)
    title = module_globals.get("TITLE", TITLE)

    surface = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    screen.surface = surface
    screen.draw.surface = surface

    update_fn = module_globals.get("update")
    draw_fn = module_globals.get("draw")
    on_key_down_fn = module_globals.get("on_key_down")
    on_key_up_fn = module_globals.get("on_key_up")
    on_mouse_down_fn = module_globals.get("on_mouse_down")
    on_mouse_up_fn = module_globals.get("on_mouse_up")
    on_mouse_move_fn = module_globals.get("on_mouse_move")

    pg_clock = pygame.time.Clock()
    running = True
    while running:
        dt = pg_clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and on_key_down_fn:
                _call_hook(on_key_down_fn, key=event.key, unicode=event.unicode)
            elif event.type == pygame.KEYUP and on_key_up_fn:
                _call_hook(on_key_up_fn, key=event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and on_mouse_down_fn:
                _call_hook(on_mouse_down_fn, pos=event.pos, button=event.button)
            elif event.type == pygame.MOUSEBUTTONUP and on_mouse_up_fn:
                _call_hook(on_mouse_up_fn, pos=event.pos, button=event.button)
            elif event.type == pygame.MOUSEMOTION and on_mouse_move_fn:
                _call_hook(on_mouse_move_fn, pos=event.pos, rel=event.rel, buttons=event.buttons)

        clock.tick(dt)
        if update_fn:
            _call_hook(update_fn, dt=dt)
        if draw_fn:
            draw_fn()

        pygame.display.flip()
        await asyncio.sleep(0)  # gibt die Kontrolle an den Browser zurueck

    pygame.quit()


def go():
    caller_globals = inspect.stack()[1].frame.f_globals
    asyncio.run(_run(caller_globals))
