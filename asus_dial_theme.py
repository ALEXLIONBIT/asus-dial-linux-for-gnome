"""Drawing of the ASUS Dial radial menu and on-screen messages, with themes.

Used by the driver (asus-dial) for the real thing and by asus-dial-manager for the live preview,
so what you see in the settings app is what you get on the dial.

Themes (see asus_dial_config.DEFAULT_THEME): plain color, image, rainbow and Halloween backgrounds,
plus blur (frosted glass), glow, glossy reflection, shadow and sparkles.
"""
import colorsys
import math
import random

import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo
import cairo

MENU_PAD, MENU_PAD_HALLOWEEN = 50, 110
OSD_W, OSD_H, OSD_PAD, OSD_PAD_HALLOWEEN = 360, 110, 30, 56


# ------------------------------------------------------------------ helpers
def rgb(hex_color, default=(0.5, 0.5, 0.5)):
    h = (hex_color or "").lstrip("#")
    try:
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return default


def is_animated(theme):
    return theme.get("bg_type") in ("rainbow", "halloween") or bool(theme.get("sparkles"))


def menu_pad(theme):
    return MENU_PAD_HALLOWEEN if theme.get("bg_type") == "halloween" else MENU_PAD


def osd_pad(theme):
    return OSD_PAD_HALLOWEEN if theme.get("bg_type") == "halloween" else OSD_PAD


def text(cr, s, size, x, y, center=True, bold=False):
    """Pango text (glyph fallback for emoji); y is the vertical centre."""
    layout = PangoCairo.create_layout(cr)
    layout.set_font_description(Pango.FontDescription(f"Sans {'Bold ' if bold else ''}{size}"))
    layout.set_text(s, -1)
    w, h = layout.get_pixel_size()
    cr.move_to(x - w / 2 if center else x, y - h / 2)
    PangoCairo.show_layout(cr, layout)


def capture_backdrop(x, y, w, h, radius):
    """A blurred snapshot of the screen area x, y, w, h as a cairo surface (None if Pillow or the grab is unavailable)."""
    try:
        from PIL import ImageFilter, ImageGrab
        im = ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGBA").filter(ImageFilter.GaussianBlur(radius))
        data = bytearray(im.tobytes("raw", "BGRA"))
        return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
    except Exception:
        return None


_images = {}


def load_image(path):
    if not path:
        return None
    if path not in _images:
        try:
            _images[path] = cairo.ImageSurface.create_from_png(path)
        except Exception:
            _images[path] = None
    return _images[path]


def _star4(cr, x, y, sz):
    """A four-point sparkle."""
    k = sz * 0.1
    cr.move_to(x, y - sz)
    cr.curve_to(x + k, y - k, x + k, y - k, x + sz, y)
    cr.curve_to(x + k, y + k, x + k, y + k, x, y + sz)
    cr.curve_to(x - k, y + k, x - k, y + k, x - sz, y)
    cr.curve_to(x - k, y - k, x - k, y - k, x, y - sz)
    cr.close_path()


def _rounded(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def _sparkles(cr, cx, cy, radius, t, speed, color=(1, 1, 0.9), count=46, seed=7):
    rnd = random.Random(seed)
    for _ in range(count):
        ang, dist, ph, sz = rnd.uniform(0, 6.283), math.sqrt(rnd.random()) * 0.95, rnd.uniform(0, 6.283), rnd.uniform(0.012, 0.03)
        tw = 0.5 + 0.5 * math.sin(t * (2 + 3 * speed) + ph * 3)
        if tw < 0.15:
            continue
        _star4(cr, cx + math.cos(ang) * dist * radius, cy + math.sin(ang) * dist * radius, sz * radius * (0.5 + tw))
        cr.set_source_rgba(*color, 0.9 * tw)
        cr.fill()


# ------------------------------------------------------------------ backgrounds
def _bg_rainbow(cr, cx, cy, r, t, speed, opacity):
    n = 96
    for i in range(n):
        a0, a1 = i * 2 * math.pi / n, (i + 1.15) * 2 * math.pi / n
        cr.move_to(cx, cy)
        cr.arc(cx, cy, r, a0, a1)
        cr.close_path()
        h = (i / n + t * 0.12 * (0.3 + speed)) % 1.0
        cr.set_source_rgba(*colorsys.hsv_to_rgb(h, 0.75, 1.0), opacity)
        cr.fill()
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)  # soften the middle and keep the text readable
    g.add_color_stop_rgba(0, 0.05, 0.05, 0.1, 0.55)
    g.add_color_stop_rgba(0.6, 0.05, 0.05, 0.1, 0.3)
    g.add_color_stop_rgba(1, 0.05, 0.05, 0.1, 0.12)
    cr.set_source(g)
    cr.arc(cx, cy, r, 0, 2 * math.pi)
    cr.fill()


def _bg_image(cr, cx, cy, r, theme, opacity):
    img = load_image(theme.get("bg_image"))
    if img is None:
        cr.set_source_rgba(0.08, 0.08, 0.1, opacity)
        cr.paint()
        return
    cr.save()
    cr.translate(cx - r, cy - r)
    cr.scale(2 * r / img.get_width(), 2 * r / img.get_height())
    cr.set_source_surface(img, 0, 0)
    cr.paint_with_alpha(opacity)
    cr.restore()
    cr.set_source_rgba(0, 0, 0, theme.get("image_dim", 0.35))
    cr.arc(cx, cy, r, 0, 2 * math.pi)
    cr.fill()


# ------------------------------------------------------------------ Halloween artwork
def _ghost(cr, x, y, s, t, phase=0.0, alpha=0.9):
    """A friendly ghost; x, y = centre, s = width."""
    bob = math.sin(t * 2 + phase) * s * 0.08
    w, h = s, s * 1.2
    cr.save()
    cr.translate(x, y + bob)
    cr.rotate(math.sin(t * 1.3 + phase) * 0.08)
    cr.new_path()
    cr.move_to(-w / 2, h / 2)
    cr.line_to(-w / 2, -h * 0.05)
    cr.curve_to(-w / 2, -h * 0.65, w / 2, -h * 0.65, w / 2, -h * 0.05)
    cr.line_to(w / 2, h / 2)
    n = 4
    step = w / n
    for i in range(n):
        xa = w / 2 - step * i
        d = s * 0.16 * (1 + 0.35 * math.sin(t * 3 + i + phase))
        cr.curve_to(xa, h / 2 + d, xa - step, h / 2 + d, xa - step, h / 2)
    cr.close_path()
    g = cairo.LinearGradient(0, -h / 2, 0, h / 2)
    g.add_color_stop_rgba(0, 1, 1, 1, alpha)
    g.add_color_stop_rgba(1, 0.8, 0.85, 1, alpha * 0.8)
    cr.set_source(g)
    cr.fill_preserve()
    cr.set_source_rgba(0.6, 0.65, 0.9, alpha * 0.6)
    cr.set_line_width(max(1.0, s * 0.02))
    cr.stroke()
    cr.set_source_rgba(0.08, 0.05, 0.15, alpha)
    for ex in (-0.2, 0.2):
        cr.save()
        cr.translate(ex * w, -h * 0.12)
        cr.scale(0.07 * w, 0.11 * w)
        cr.arc(0, 0, 1, 0, 2 * math.pi)
        cr.restore()
        cr.fill()
    cr.save()
    cr.translate(0, h * 0.1)
    cr.scale(0.07 * w, 0.09 * w * (1 + 0.3 * math.sin(t * 4 + phase)))
    cr.arc(0, 0, 1, 0, 2 * math.pi)
    cr.restore()
    cr.fill()
    cr.restore()


def _tombstone(cr, x, y, s, t, kind=0, eyes=False, phase=0.0):
    """x, y = bottom centre, s = width."""
    h = s * 1.3
    cr.save()
    cr.translate(x, y)
    cr.new_path()
    cr.move_to(-s / 2, 0)
    cr.line_to(-s / 2, -h + s / 2)
    cr.arc(0, -h + s / 2, s / 2, math.pi, 0)
    cr.line_to(s / 2, 0)
    cr.close_path()
    g = cairo.LinearGradient(-s / 2, -h, s / 2, 0)
    g.add_color_stop_rgb(0, 0.66, 0.68, 0.74)
    g.add_color_stop_rgb(1, 0.34, 0.36, 0.43)
    cr.set_source(g)
    cr.fill_preserve()
    cr.set_source_rgb(0.14, 0.12, 0.2)
    cr.set_line_width(max(1.5, s * 0.05))
    cr.stroke()
    cr.set_source_rgb(0.16, 0.14, 0.22)
    if kind == 1:  # cross
        cr.set_line_width(max(2.0, s * 0.09))
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(0, -h * 0.82)
        cr.line_to(0, -h * 0.35)
        cr.move_to(-s * 0.2, -h * 0.65)
        cr.line_to(s * 0.2, -h * 0.65)
        cr.stroke()
    else:
        text(cr, "RIP", max(5, int(s * 0.22)), 0, -h * 0.55, bold=True)
    cr.set_source_rgba(0.25, 0.55, 0.25, 0.85)  # moss
    for mx, mr in ((-0.3, 0.1), (0.05, 0.07), (0.32, 0.09)):
        cr.arc(mx * s, -s * 0.03, mr * s, math.pi, 2 * math.pi)
        cr.fill()
    if eyes:  # glowing eyes peeking out
        fl = 0.6 + 0.4 * math.sin(t * 6 + phase)
        for ex in (-0.16, 0.16):
            gl = cairo.RadialGradient(ex * s, -h * 0.86, 0, ex * s, -h * 0.86, s * 0.18)
            gl.add_color_stop_rgba(0, 1, 0.2, 0.1, fl)
            gl.add_color_stop_rgba(1, 1, 0.2, 0.1, 0)
            cr.set_source(gl)
            cr.arc(ex * s, -h * 0.86, s * 0.18, 0, 2 * math.pi)
            cr.fill()
    cr.restore()


def _skeleton(cr, x, y, s, t, phase=0.0):
    """A dancing skeleton; x, y = between the feet, s = height."""
    sw = math.sin(t * 4 + phase)
    bone, dark = (0.96, 0.95, 0.88), (0.1, 0.08, 0.16)
    cr.save()
    cr.translate(x + sw * s * 0.03, y)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)

    def limb(points, w):
        for color, width in ((dark, w * 1.7), (bone, w)):
            cr.set_source_rgb(*color)
            cr.set_line_width(width)
            cr.move_to(*points[0])
            for p in points[1:]:
                cr.line_to(*p)
            cr.stroke()

    lw = s * 0.035
    hip = (0, -s * 0.38)
    for side in (-1, 1):  # legs: one kicks
        k = math.sin(t * 4 + phase + (0 if side < 0 else math.pi)) * 0.35
        knee = (side * s * 0.06 + k * s * 0.1, -s * 0.2)
        foot = (side * s * 0.09 + k * s * 0.2, 0)
        limb([hip, knee, foot], lw)
    limb([(0, -s * 0.72), hip], lw * 1.1)  # spine
    for i, wd in enumerate((0.2, 0.18, 0.14)):  # ribs
        yy = -s * (0.66 - 0.06 * i)
        limb([(-s * wd / 2, yy), (s * wd / 2, yy)], lw * 0.7)
    shoulder_y = -s * 0.68
    limb([(-s * 0.1, shoulder_y), (-s * 0.17, -s * 0.55 + sw * s * 0.03), (-s * 0.14, -s * 0.44 + sw * s * 0.05)], lw)
    wave = math.sin(t * 6 + phase)  # right arm waves above the head
    limb([(s * 0.1, shoulder_y), (s * 0.2, -s * 0.78), (s * 0.18 + wave * s * 0.05, -s * 0.95)], lw)
    limb([(-s * 0.1, -s * 0.38), (s * 0.1, -s * 0.38)], lw * 1.2)  # pelvis
    head = (0, -s * 0.82)
    cr.arc(*head, s * 0.115, 0, 2 * math.pi)  # skull
    cr.set_source_rgb(*bone)
    cr.fill_preserve()
    cr.set_source_rgb(*dark)
    cr.set_line_width(lw * 0.8)
    cr.stroke()
    cr.set_source_rgb(*dark)
    for ex in (-0.045, 0.045):
        cr.arc(head[0] + ex * s, head[1] - s * 0.01, s * 0.03, 0, 2 * math.pi)
        cr.fill()
    cr.move_to(head[0], head[1] + s * 0.02)  # nose
    cr.line_to(head[0] - s * 0.012, head[1] + s * 0.05)
    cr.line_to(head[0] + s * 0.012, head[1] + s * 0.05)
    cr.fill()
    cr.set_line_width(lw * 0.45)  # teeth
    for tx in (-0.04, -0.013, 0.013, 0.04):
        cr.move_to(head[0] + tx * s, head[1] + s * 0.07)
        cr.line_to(head[0] + tx * s, head[1] + s * 0.098)
    cr.stroke()
    cr.restore()


def _pumpkin(cr, x, y, s, t, phase=0.0):
    """A jack-o'-lantern; x, y = bottom centre, s = width."""
    h = s * 0.82
    cr.save()
    cr.translate(x, y - h / 2)
    fl = 0.8 + 0.2 * math.sin(t * 9 + phase)
    gl = cairo.RadialGradient(0, 0, 0, 0, 0, s * 0.9)
    gl.add_color_stop_rgba(0, 1, 0.6, 0.1, 0.35 * fl)
    gl.add_color_stop_rgba(1, 1, 0.5, 0.0, 0)
    cr.set_source(gl)
    cr.arc(0, 0, s * 0.9, 0, 2 * math.pi)
    cr.fill()
    for dx, wd in ((-0.28, 0.5), (0.28, 0.5), (0, 0.55)):  # lobes
        cr.save()
        cr.translate(dx * s, 0)
        cr.scale(wd * s / 2, h / 2)
        cr.arc(0, 0, 1, 0, 2 * math.pi)
        cr.restore()
        g = cairo.LinearGradient(0, -h / 2, 0, h / 2)
        g.add_color_stop_rgb(0, 1.0, 0.62, 0.12)
        g.add_color_stop_rgb(1, 0.85, 0.35, 0.04)
        cr.set_source(g)
        cr.fill_preserve()
        cr.set_source_rgb(0.45, 0.18, 0.02)
        cr.set_line_width(max(1.0, s * 0.025))
        cr.stroke()
    cr.set_source_rgb(0.25, 0.4, 0.12)  # stem
    cr.rectangle(-s * 0.05, -h / 2 - s * 0.14, s * 0.1, s * 0.16)
    cr.fill()
    cr.set_source_rgba(1, 0.9, 0.3, fl)  # glowing face
    for ex in (-0.2, 0.2):
        cr.move_to(ex * s, -h * 0.28)
        cr.line_to(ex * s - s * 0.09, -h * 0.02)
        cr.line_to(ex * s + s * 0.09, -h * 0.02)
        cr.close_path()
        cr.fill()
    cr.move_to(0, h * 0.02)
    cr.line_to(-s * 0.05, h * 0.12)
    cr.line_to(s * 0.05, h * 0.12)
    cr.close_path()
    cr.fill()
    cr.move_to(-s * 0.3, h * 0.2)
    for i, px in enumerate((-0.2, -0.1, 0.0, 0.1, 0.2, 0.3)):
        cr.line_to(px * s, h * (0.3 if i % 2 == 0 else 0.2))
    cr.line_to(s * 0.3, h * 0.2)
    cr.line_to(s * 0.3, h * 0.28)
    cr.line_to(-s * 0.3, h * 0.28)
    cr.close_path()
    cr.fill()
    cr.restore()


def _bat(cr, x, y, s, t, phase=0.0):
    f = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 13 + phase))  # wing flap
    cr.save()
    cr.translate(x, y)
    cr.set_source_rgb(0.05, 0.02, 0.09)
    for side in (-1, 1):
        cr.move_to(0, -s * 0.05)
        cr.curve_to(side * s * 0.3, -s * 0.55 * f, side * s * 0.7, -s * 0.45 * f, side * s, -s * 0.2 * f)
        cr.curve_to(side * s * 0.88, s * 0.08, side * s * 0.75, s * 0.02, side * s * 0.65, s * 0.18)
        cr.curve_to(side * s * 0.52, s * 0.04, side * s * 0.38, s * 0.12, side * s * 0.25, s * 0.2)
        cr.line_to(0, s * 0.12)
        cr.close_path()
        cr.fill()
    cr.save()
    cr.scale(s * 0.13, s * 0.2)
    cr.arc(0, 0, 1, 0, 2 * math.pi)
    cr.restore()
    cr.fill()
    for side in (-1, 1):
        cr.move_to(side * s * 0.06, -s * 0.14)
        cr.line_to(side * s * 0.1, -s * 0.3)
        cr.line_to(side * s * 0.14, -s * 0.12)
        cr.fill()
        cr.arc(side * s * 0.055, -s * 0.06, s * 0.025, 0, 2 * math.pi)
        cr.set_source_rgb(1, 0.2, 0.1)
        cr.fill()
        cr.set_source_rgb(0.05, 0.02, 0.09)
    cr.restore()


def _spider(cr, x, y0, length, t):
    ln = length * (0.85 + 0.15 * math.sin(t * 1.4))
    cr.set_source_rgba(1, 1, 1, 0.55)
    cr.set_line_width(1.2)
    cr.move_to(x, y0)
    cr.line_to(x, y0 + ln)
    cr.stroke()
    cr.save()
    cr.translate(x, y0 + ln + 9)
    cr.set_source_rgb(0.07, 0.04, 0.1)
    cr.set_line_width(1.8)
    for i in range(4):
        for side in (-1, 1):
            a = (i - 1.5) * 0.45
            kx, ky = side * 13, a * 12 - 4
            cr.move_to(side * 4, a * 3)
            cr.line_to(kx, ky)
            cr.line_to(side * 17, ky + 9)
    cr.stroke()
    cr.arc(0, 2, 8, 0, 2 * math.pi)
    cr.fill()
    cr.arc(0, -6, 5, 0, 2 * math.pi)
    cr.fill()
    cr.set_source_rgb(1, 0.15, 0.1)
    for ex in (-2, 2):
        cr.arc(ex, -7, 1.3, 0, 2 * math.pi)
        cr.fill()
    cr.restore()


def _cobweb(cr, x, y, size, flip_x=1, flip_y=1):
    cr.save()
    cr.translate(x, y)
    cr.scale(flip_x, flip_y)
    cr.set_source_rgba(1, 1, 1, 0.55)
    cr.set_line_width(1.1)
    angs = [i * math.pi / 8 for i in range(5)]
    for a in angs:
        cr.move_to(0, 0)
        cr.line_to(size * math.cos(a), size * math.sin(a))
    cr.stroke()
    for frac in (0.3, 0.52, 0.76, 1.0):
        r = size * frac
        cr.move_to(r * math.cos(angs[0]), r * math.sin(angs[0]))
        for a0, a1 in zip(angs, angs[1:]):
            am = (a0 + a1) / 2
            cr.curve_to(r * 0.8 * math.cos(am), r * 0.8 * math.sin(am), r * 0.8 * math.cos(am), r * 0.8 * math.sin(am),
                        r * math.cos(a1), r * math.sin(a1))
        cr.stroke()
    cr.restore()


def _moon(cr, x, y, r, alpha=1.0):
    gl = cairo.RadialGradient(x, y, r * 0.8, x, y, r * 2)
    gl.add_color_stop_rgba(0, 1, 0.95, 0.7, 0.35 * alpha)
    gl.add_color_stop_rgba(1, 1, 0.95, 0.7, 0)
    cr.set_source(gl)
    cr.arc(x, y, r * 2, 0, 2 * math.pi)
    cr.fill()
    g = cairo.RadialGradient(x - r * 0.3, y - r * 0.3, 0, x, y, r)
    g.add_color_stop_rgba(0, 1, 1, 0.88, alpha)
    g.add_color_stop_rgba(1, 0.95, 0.88, 0.6, alpha)
    cr.set_source(g)
    cr.arc(x, y, r, 0, 2 * math.pi)
    cr.fill()
    cr.set_source_rgba(0.8, 0.72, 0.45, 0.45 * alpha)
    for dx, dy, rr in ((-0.3, -0.2, 0.18), (0.25, 0.1, 0.22), (-0.1, 0.4, 0.12)):
        cr.arc(x + dx * r, y + dy * r, rr * r, 0, 2 * math.pi)
        cr.fill()


def _halloween_disc(cr, cx, cy, r, t, speed, opacity):
    """Inside the menu disc: night sky, moon, stars, drifting mist, bats and ghosts."""
    g = cairo.RadialGradient(cx, cy - r * 0.2, 0, cx, cy, r)
    g.add_color_stop_rgba(0, 0.28, 0.1, 0.38, opacity)
    g.add_color_stop_rgba(0.7, 0.12, 0.04, 0.2, opacity)
    g.add_color_stop_rgba(1, 0.04, 0.01, 0.08, opacity)
    cr.set_source(g)
    cr.arc(cx, cy, r, 0, 2 * math.pi)
    cr.fill()
    _sparkles(cr, cx, cy, r, t, speed, color=(1, 0.9, 0.6), count=30, seed=11)
    for k in range(3):  # mist
        mx = cx + ((t * 14 * (0.5 + speed) + k * r * 0.9) % (2.6 * r)) - 1.3 * r
        my = cy + r * (0.55 + 0.12 * k)
        mg = cairo.RadialGradient(mx, my, 0, mx, my, r * 0.55)
        mg.add_color_stop_rgba(0, 0.8, 0.75, 1, 0.16)
        mg.add_color_stop_rgba(1, 0.8, 0.75, 1, 0)
        cr.set_source(mg)
        cr.save()
        cr.translate(mx, my)
        cr.scale(1, 0.35)
        cr.translate(-mx, -my)
        cr.arc(mx, my, r * 0.55, 0, 2 * math.pi)
        cr.restore()
        cr.fill()
    for k in range(2):  # bats crossing the disc
        u = ((t * 0.16 * (0.5 + speed) + k * 0.5) % 1.0)
        _bat(cr, cx - r * 1.1 + u * r * 2.2, cy - r * (0.55 - 0.25 * k) + math.sin(u * 14) * r * 0.05, r * 0.11, t, phase=k * 2)
    for k in range(2):  # translucent ghosts drifting behind the slices
        u = ((t * 0.05 * (0.5 + speed) + k * 0.5) % 1.0)
        _ghost(cr, cx + (-0.8 + 1.6 * (u if k == 0 else 1 - u)) * r, cy + r * (0.15 - 0.35 * k), r * 0.15, t, phase=k * 3, alpha=0.18)


def _halloween_frame(cr, pad, size_w, size_h, cx_disc, cy_disc, r_disc, t, speed):
    """Around the menu: graveyard with skeleton and pumpkins at the bottom, cobwebs, spider, moon-lit ghosts and bats."""
    w, h = size_w, size_h
    # ground
    cr.save()
    cr.rectangle(0, h - pad * 0.38, w, pad * 0.38)
    cr.clip()
    g = cairo.LinearGradient(0, h - pad * 0.4, 0, h)
    g.add_color_stop_rgb(0, 0.13, 0.06, 0.2)
    g.add_color_stop_rgb(1, 0.05, 0.02, 0.08)
    cr.set_source(g)
    cr.paint()
    cr.restore()
    base = h - pad * 0.1
    # bottom corners: skeleton (left), pumpkins (right), tombstones between
    _skeleton(cr, pad * 0.9, base, pad * 1.45, t, 0)
    _tombstone(cr, pad * 1.95, base, pad * 0.5, t, 0, True, 0)
    _tombstone(cr, w - pad * 2.1, base, pad * 0.46, t, 1, True, 2)
    _tombstone(cr, w * 0.5 - pad * 0.3, base + 2, pad * 0.4, t, 0, False)
    _tombstone(cr, w * 0.5 + pad * 0.5, base + 2, pad * 0.36, t, 1, False)
    _pumpkin(cr, w - pad * 1.0, base + 4, pad * 0.95, t, 1)
    _pumpkin(cr, w - pad * 1.75, base + 6, pad * 0.5, t, 2)
    # top corners
    _cobweb(cr, 0, 0, pad * 1.5)
    _cobweb(cr, w, 0, pad * 1.5, flip_x=-1)
    _spider(cr, pad * 1.55, 0, pad * 0.95, t)
    _moon(cr, w - pad * 0.95, pad * 0.95, pad * 0.3, 0.95)
    # sides: ghosts
    _ghost(cr, pad * 0.5, h * 0.4, pad * 0.62, t, 0.5, 0.88)
    _ghost(cr, w - pad * 0.48, h * 0.62, pad * 0.55, t, 2.2, 0.85)
    # bats flying around
    for k in range(3):
        u = (t * 0.1 * (0.5 + speed) + k / 3) % 1.0
        _bat(cr, -pad * 0.3 + u * (w + pad * 0.6), pad * (0.35 + 0.5 * k) + math.sin(u * 20 + k) * pad * 0.18, pad * 0.34, t, phase=k * 1.7)


def _halloween_osd_frame(cr, pad, w, h, t, speed):
    """Around the little message box: pumpkin, ghost, bat, spider, tiny graveyard."""
    bx, by, bw, bh = pad, pad, w - 2 * pad, h - 2 * pad
    _pumpkin(cr, bx + pad * 0.8, by + 6, pad * 0.9, t, 0)
    _ghost(cr, bx + bw - pad * 0.6, by - pad * 0.1, pad * 0.75, t, 1.5, 0.9)
    _spider(cr, bx + bw * 0.5, 0, by - 2, t)
    u = (t * 0.2 * (0.5 + speed)) % 1.0
    _bat(cr, u * w, pad * 0.35 + math.sin(u * 16) * pad * 0.12, pad * 0.4, t)
    base = by + bh + pad * 0.78
    for i, kx in enumerate((0.12, 0.3, 0.62, 0.84)):
        _tombstone(cr, bx + bw * kx, base, pad * 0.38, t, i % 2, i == 0, i)
    _skeleton(cr, bx + bw * 0.48, base + 2, pad * 0.9, t, 1)


# ------------------------------------------------------------------ the menu
def draw_menu(cr, theme, items, sel, t, msize, backdrop=None):
    """items: [(icon, name)]. cr origin = top-left of the window (size msize + 2 * pad)."""
    pad = menu_pad(theme)
    R = msize / 2
    cx = cy = pad + R
    Wd = msize + 2 * pad
    halloween = theme["bg_type"] == "halloween"
    tc = rgb(theme["text"], (1, 1, 1))
    accent = rgb(theme["accent"], (0.25, 0.55, 1.0))
    r_disc, r_out, r_in = R - 5, R - 10, 105
    r_txt = r_in + 0.53 * (r_out - r_in)
    n = max(1, len(items))

    if theme["shadow"]:  # soft shadow under the disc
        s = theme["shadow_strength"]
        g = cairo.RadialGradient(cx, cy + 8, r_disc * 0.88, cx, cy + 8, r_disc + pad * 0.85)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.6 * s)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        cr.set_source(g)
        cr.arc(cx, cy + 8, r_disc + pad * 0.85, 0, 2 * math.pi)
        cr.fill()
    if theme["glow"]:  # glowing rim
        gc = rgb(theme["glow_color"], accent)
        g = cairo.RadialGradient(cx, cy, r_disc * 0.96, cx, cy, r_disc + pad * 0.7)
        g.add_color_stop_rgba(0, *gc, 0.7 * theme["glow_strength"])
        g.add_color_stop_rgba(1, *gc, 0)
        cr.set_source(g)
        cr.arc(cx, cy, r_disc + pad * 0.7, 0, 2 * math.pi)
        cr.fill()

    cr.save()  # ---- disc content
    cr.arc(cx, cy, r_disc, 0, 2 * math.pi)
    cr.clip()
    if backdrop is not None:
        cr.set_source_surface(backdrop, 0, 0)
        cr.paint()
    op = theme["bg_opacity"]
    kind = theme["bg_type"]
    if kind == "rainbow":
        _bg_rainbow(cr, cx, cy, r_disc, t, theme["speed"], op)
    elif kind == "image":
        _bg_image(cr, cx, cy, r_disc, theme, op)
    elif kind == "halloween":
        _halloween_disc(cr, cx, cy, r_disc, t, theme["speed"], op)
    else:
        cr.set_source_rgba(*rgb(theme["bg_color"], (0.08, 0.08, 0.1)), op)
        cr.paint()
    for i in range(n):  # slices
        a0 = -math.pi / 2 + (i - 0.5) * 2 * math.pi / n
        a1 = a0 + 2 * math.pi / n
        cr.new_path()
        cr.arc(cx, cy, r_out, a0 + 0.02, a1 - 0.02)
        cr.arc_negative(cx, cy, r_in, a1 - 0.02, a0 + 0.02)
        cr.close_path()
        if i == sel:
            if theme["glow"]:
                gc = rgb(theme["glow_color"], accent)
                cr.set_line_join(cairo.LINE_JOIN_ROUND)
                for lw, al in ((26, 0.08), (16, 0.14), (8, 0.22)):
                    cr.set_source_rgba(*gc, al * (0.4 + theme["glow_strength"]))
                    cr.set_line_width(lw)
                    cr.stroke_preserve()
            cr.set_source_rgba(*accent, 0.95)
        else:
            cr.set_source_rgba(*tc, 0.07 if kind != "halloween" else 0.05)
        cr.fill()
    if theme["reflection"] > 0:  # glossy highlight on the upper part
        k = theme["reflection"]
        cr.save()
        cr.save()
        cr.translate(cx, cy - r_disc * 0.42)
        cr.scale(r_disc * 0.92, r_disc * 0.55)
        cr.arc(0, 0, 1, 0, 2 * math.pi)
        cr.restore()
        g = cairo.LinearGradient(0, cy - r_disc, 0, cy)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.42 * k)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        cr.set_source(g)
        cr.fill()
        cr.restore()
        cr.set_line_width(2)
        cr.arc(cx, cy, r_disc - 2, math.pi * 1.1, math.pi * 1.9)
        cr.set_source_rgba(1, 1, 1, 0.35 * k)
        cr.stroke()
    if theme["sparkles"] and kind != "halloween":
        _sparkles(cr, cx, cy, r_disc, t, theme["speed"], seed=3)
    if kind == "rainbow":
        _sparkles(cr, cx, cy, r_disc, t, theme["speed"], seed=5, count=34)
    for i, (icon, name) in enumerate(items):  # icons and names
        am = -math.pi / 2 + i * 2 * math.pi / n
        tx, ty = cx + r_txt * math.cos(am), cy + r_txt * math.sin(am)
        cr.set_source_rgba(*tc, 1)
        text(cr, icon, 20, tx, ty - 11)
        text(cr, name, 9, tx, ty + 17)
    if items:
        cr.set_source_rgba(*tc, 0.92)
        text(cr, items[min(sel, len(items) - 1)][1], 13, cx, cy)
    cr.restore()

    if halloween:
        _halloween_frame(cr, pad, Wd, Wd, cx, cy, r_disc, t, theme["speed"])


# ------------------------------------------------------------------ the on-screen message
def draw_osd(cr, theme, label, value, t, backdrop=None):
    """cr origin = top-left of the window (size OSD_W + 2 pad, OSD_H + 2 pad)."""
    pad = osd_pad(theme)
    w, h, r = OSD_W, OSD_H, 22
    x0, y0 = pad, pad
    tc = rgb(theme["text"], (1, 1, 1))
    accent = rgb(theme["accent"], (0.25, 0.55, 1.0))
    kind = theme["bg_type"]

    def box():
        cr.new_sub_path()
        cr.arc(x0 + w - r, y0 + r, r, -math.pi / 2, 0)
        cr.arc(x0 + w - r, y0 + h - r, r, 0, math.pi / 2)
        cr.arc(x0 + r, y0 + h - r, r, math.pi / 2, math.pi)
        cr.arc(x0 + r, y0 + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    if theme["shadow"]:
        s = theme["shadow_strength"]
        for grow, al in ((14, 0.05), (9, 0.08), (5, 0.12), (2, 0.16)):
            _rounded(cr, x0 - grow, y0 - grow + 5, w + 2 * grow, h + 2 * grow, r + grow)
            cr.set_source_rgba(0, 0, 0, al * s * 1.6)
            cr.fill()
    if theme["glow"]:
        gc = rgb(theme["glow_color"], accent)
        for grow, al in ((14, 0.05), (9, 0.09), (5, 0.14), (2, 0.2)):
            _rounded(cr, x0 - grow, y0 - grow, w + 2 * grow, h + 2 * grow, r + grow)
            cr.set_source_rgba(*gc, al * theme["glow_strength"] * 1.4)
            cr.fill()
    cr.save()
    box()
    cr.clip()
    if backdrop is not None:
        cr.set_source_surface(backdrop, 0, 0)
        cr.paint()
    op = theme["bg_opacity"]
    if kind == "rainbow":
        _bg_rainbow(cr, x0 + w / 2, y0 + h / 2, w * 0.62, t, theme["speed"], op)
        cr.set_source_rgba(0.05, 0.05, 0.1, 0.35)
        cr.paint()
    elif kind == "image":
        _bg_image(cr, x0 + w / 2, y0 + h / 2, w / 2, theme, op)
    elif kind == "halloween":
        g = cairo.LinearGradient(x0, y0, x0 + w, y0 + h)
        g.add_color_stop_rgba(0, 0.22, 0.08, 0.32, op)
        g.add_color_stop_rgba(1, 0.06, 0.02, 0.1, op)
        cr.set_source(g)
        cr.paint()
        _sparkles(cr, x0 + w / 2, y0 + h / 2, w * 0.45, t, theme["speed"], color=(1, 0.9, 0.6), count=14, seed=2)
    else:
        cr.set_source_rgba(*rgb(theme["bg_color"], (0.08, 0.08, 0.1)), op)
        cr.paint()
    if theme["reflection"] > 0:
        k = theme["reflection"]
        g = cairo.LinearGradient(0, y0, 0, y0 + h * 0.55)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.35 * k)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        cr.set_source(g)
        cr.rectangle(x0, y0, w, h * 0.55)
        cr.fill()
    if theme["sparkles"] and kind != "halloween":
        _sparkles(cr, x0 + w / 2, y0 + h / 2, w * 0.5, t, theme["speed"], seed=4, count=20)
    cr.restore()

    cr.set_source_rgba(*tc, 1)
    has_bar = value is not None
    text(cr, label, 15, x0 + 24, y0 + (34 if has_bar else h / 2), center=False)
    if has_bar:
        cr.set_source_rgba(*tc, 0.2)
        cr.rectangle(x0 + 24, y0 + 66, w - 48, 12)
        cr.fill()
        cr.set_source_rgba(*accent, 1)
        cr.rectangle(x0 + 24, y0 + 66, (w - 48) * max(0.0, min(1.0, value)), 12)
        cr.fill()
    if kind == "halloween":
        _halloween_osd_frame(cr, pad, w + 2 * pad, h + 2 * pad, t, theme["speed"])
