"""Procedural texture generation with numpy (bundled with Blender).

Produces self-created images only -> no licensing questions.
The manuscript ink is an ABSTRACT, illegible imitation of vertical
column writing. It is deliberately not real text: per the director pack
we must not fake the 1924 manuscript. When a rights-cleared scan exists,
pass it to the scene builder with --manuscript-image and it replaces this.
"""
import os

import bpy
import numpy as np


# --------------------------------------------------------------------------
# small numpy utilities
# --------------------------------------------------------------------------
def _value_noise(h, w, cell, rng):
    """Smooth value noise: random grid upsampled with bicubic-ish smoothstep."""
    gh, gw = h // cell + 2, w // cell + 2
    grid = rng.random((gh, gw)).astype(np.float32)
    ys = np.linspace(0, gh - 1.001, h, dtype=np.float32)
    xs = np.linspace(0, gw - 1.001, w, dtype=np.float32)
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = grid[y0][:, x0]
    b = grid[y0][:, x0 + 1]
    c = grid[y0 + 1][:, x0]
    d = grid[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(h, w, rng, base_cell=256, octaves=5, gain=0.5):
    out = np.zeros((h, w), np.float32)
    amp, total, cell = 1.0, 0.0, base_cell
    for _ in range(octaves):
        out += amp * _value_noise(h, w, max(2, cell), rng)
        total += amp
        amp *= gain
        cell //= 2
    return out / total


def _blur(img, radius):
    """Separable box blur repeated 3x (~gaussian)."""
    if radius < 1:
        return img
    k = int(radius)
    out = img.astype(np.float32)
    for _ in range(3):
        for axis in (0, 1):
            c = np.cumsum(np.pad(out, [(k + 1, k) if a == axis else (0, 0) for a in range(2)],
                                 mode="edge"), axis=axis)
            if axis == 0:
                out = (c[2 * k + 1:] - c[:-2 * k - 1]) / (2 * k + 1)
            else:
                out = (c[:, 2 * k + 1:] - c[:, :-2 * k - 1]) / (2 * k + 1)
    return out


class Canvas:
    """Float mask canvas with anti-aliased round-brush strokes."""

    def __init__(self, h, w):
        self.h, self.w = h, w
        self.a = np.zeros((h, w), np.float32)

    def segment(self, p0, p1, r0, r1=None):
        r1 = r0 if r1 is None else r1
        (x0, y0), (x1, y1) = p0, p1
        pad = max(r0, r1) + 2
        xa, xb = int(max(0, min(x0, x1) - pad)), int(min(self.w, max(x0, x1) + pad + 1))
        ya, yb = int(max(0, min(y0, y1) - pad)), int(min(self.h, max(y0, y1) + pad + 1))
        if xa >= xb or ya >= yb:
            return
        yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy + 1e-6
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
        px, py = x0 + t * dx, y0 + t * dy
        d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
        r = r0 + (r1 - r0) * t
        cov = np.clip(r - d + 0.5, 0, 1)
        sub = self.a[ya:yb, xa:xb]
        np.maximum(sub, cov, out=sub)

    def polyline(self, pts, radii):
        for i in range(len(pts) - 1):
            self.segment(pts[i], pts[i + 1], radii[i], radii[i + 1])


def _bezier(p0, p1, p2, p3, n=10):
    t = np.linspace(0, 1, n)[:, None]
    pts = ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3
    return [tuple(p) for p in pts]


# --------------------------------------------------------------------------
# Abstract vertical-column "script"
# --------------------------------------------------------------------------
def _wedge(cv, base, tip, r_base, r_tip=0.3, n=6, bend=0.0):
    """Brush wedge: thick where the brush lands, tapering at the tip."""
    (bx, by), (tx, ty) = base, tip
    mx, my = (bx + tx) / 2, (by + ty) / 2 + bend
    pts = _bezier(np.array([bx, by]), np.array([mx, my]), np.array([mx, my]), np.array([tx, ty]), n)
    cv.polyline(pts, np.linspace(r_base, r_tip, n))


def _write_column(cv, rng, x, y_top, y_bot, scale):
    """Columns are written top->bottom, columns ordered left->right (like
    traditional Mongolian script) but the glyphs are invented abstractions:
    illegible on purpose."""
    y = y_top
    pen = 1.25 * scale
    while y < y_bot - 30 * scale:
        n_el = int(rng.integers(3, 8))
        y_word0 = y
        # word-initial crown stroke
        _wedge(cv, (x, y), (x - 6 * scale, y - 4 * scale), pen * 1.5, pen * 0.4)
        for _ in range(n_el):
            step = rng.uniform(9, 14) * scale
            kind = rng.random()
            if kind < 0.45:      # tooth: wedge pointing left, slightly down
                L = rng.uniform(5, 9) * scale
                _wedge(cv, (x, y), (x - L, y + rng.uniform(1.5, 4) * scale),
                       pen * 1.55, pen * 0.35, bend=-1.2 * scale)
            elif kind < 0.60:    # closed loop to the right of the spine
                R = rng.uniform(2.6, 4.0) * scale
                ang = np.linspace(-np.pi / 2, 1.5 * np.pi, 16)
                pts = [(x + R * 0.95 + R * np.cos(a), y + R + R * 1.1 * np.sin(a)) for a in ang]
                rad = pen * (0.75 + 0.45 * np.abs(np.cos(ang)))
                cv.polyline(pts, rad)
                step = max(step, 2.6 * R)
            elif kind < 0.72:    # dots left of the spine
                for k in range(int(rng.integers(1, 3))):
                    cx, cy = x - rng.uniform(5, 8) * scale, y + k * 4 * scale
                    cv.segment((cx, cy), (cx - 0.8 * scale, cy + 1.2 * scale), pen * 1.0)
            elif kind < 0.86:    # bow to the right
                L = rng.uniform(6, 9) * scale
                pts = _bezier(np.array([x, y]), np.array([x + L, y + 1 * scale]),
                              np.array([x + L * 0.9, y + 8 * scale]), np.array([x + 0.5, y + 10 * scale]), 12)
                cv.polyline(pts, np.linspace(pen * 0.6, pen * 1.4, 12))
                step = max(step, 11 * scale)
            else:                # angular stroke to the right
                L = rng.uniform(4, 7) * scale
                _wedge(cv, (x, y), (x + L, y + 3 * scale), pen * 1.2, pen * 0.5)
            y += step
        # continuous spine (axis) of the word with pressure variation
        n = 10
        ys = np.linspace(y_word0 - 2 * scale, y, n)
        xs = x + np.cumsum(rng.normal(0, 0.18 * scale, n))
        cv.polyline(list(zip(xs, ys)), pen * (0.85 + 0.3 * rng.random(n)))
        # word-final tail sweeping down-left
        tail = rng.uniform(8, 15) * scale
        pts = _bezier(np.array([x, y]), np.array([x + 1 * scale, y + 7 * scale]),
                      np.array([x - tail * 0.5, y + 9 * scale]), np.array([x - tail, y + 3 * scale]), 12)
        cv.polyline(pts, np.linspace(pen * 1.4, pen * 0.25, 12))
        y += rng.uniform(13, 20) * scale  # gap between words


def _frame(cv, x0, y0, x1, y1, r):
    for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                   ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        cv.segment(a, b, r)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def make_manuscript_textures(out_dir, width=2048, aspect=1.414, seed=1924, version=2):
    """Returns (albedo_path, ink_mask_path). Cached on disk."""
    os.makedirs(out_dir, exist_ok=True)
    albedo_path = os.path.join(out_dir, f"manuscript_albedo_v{version}_{seed}_{width}.png")
    ink_path = os.path.join(out_dir, f"manuscript_ink_v{version}_{seed}_{width}.png")
    if os.path.exists(albedo_path) and os.path.exists(ink_path):
        return albedo_path, ink_path

    rng = np.random.default_rng(seed)
    w = width
    h = int(width * aspect)
    s = w / 1024.0

    # --- paper -------------------------------------------------------------
    base = np.array([0.91, 0.84, 0.72], np.float32)        # parchment ivory
    stain = np.array([0.66, 0.50, 0.30], np.float32)       # oxidised edge
    n1 = fbm(h, w, rng, base_cell=int(320 * s), octaves=6)
    n2 = fbm(h, w, rng, base_cell=int(90 * s), octaves=4)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / (0.09 * w)
    edge = np.clip(edge + (n2 - 0.5) * 0.8, 0, 1)
    edge_dark = (1 - edge) ** 2.2
    t = np.clip(0.25 * (n1 - 0.5) * 2 + 0.85 * edge_dark, 0, 1)
    img = base[None, None, :] * (1 - t[..., None]) + stain[None, None, :] * t[..., None]
    img *= (0.94 + 0.10 * n2)[..., None]

    # foxing / water stains: soft rings
    warp = (fbm(h, w, rng, base_cell=int(40 * s), octaves=3) - 0.5) * 0.9
    for _ in range(9):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        rad = rng.uniform(25, 110) * s
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad + warp
        ring = np.exp(-((d - 1.0) ** 2) * 10) * 0.045 + np.exp(-d * d * 1.5) * 0.04
        img *= (1 - ring * rng.uniform(0.4, 1.0))[..., None]

    # paper fibres
    fib = Canvas(h, w)
    for _ in range(int(2600 * s * s)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, np.pi)
        L = rng.uniform(3, 9) * s
        fib.segment((x, y), (x + L * np.cos(a), y + L * np.sin(a)), 0.3 * s)
    img *= (1 - 0.025 * fib.a)[..., None]

    # --- ink --------------------------------------------------------------
    ink = Canvas(h, w)
    mx, my = 0.13 * w, 0.10 * h
    _frame(ink, mx * 0.72, my * 0.78, w - mx * 0.72, h - my * 0.78, 1.6 * s)
    _frame(ink, mx * 0.80, my * 0.84, w - mx * 0.80, h - my * 0.84, 0.7 * s)
    ncols = 22
    col_w = (w - 2 * mx) / ncols
    for i in range(ncols):
        x = mx + col_w * (i + 0.62) + rng.normal(0, 1.2 * s)
        _write_column(ink, rng, x, my + rng.uniform(4, 14) * s,
                      h - my - (rng.uniform(300, 600) * s if i == ncols - 1 else rng.uniform(0, 20) * s),
                      scale=1.35 * s)

    ink_a = np.clip(ink.a, 0, 1)
    # dry-brush breakup + slight bleed into fibres
    breakup = fbm(h, w, rng, base_cell=int(6 * s) or 2, octaves=2)
    ink_a = ink_a * np.clip(0.55 + breakup * 0.9, 0, 1)
    bleed = _blur(ink_a, 1.5 * s) * 0.45
    ink_a = np.clip(np.maximum(ink_a, bleed), 0, 1)
    ink_col = np.array([0.075, 0.052, 0.04], np.float32)
    density = (0.80 + 0.2 * n2)[..., None]
    img = img * (1 - ink_a[..., None] * density) + ink_col * ink_a[..., None] * density

    _save(albedo_path, np.clip(img, 0, 1), srgb=True)
    _save(ink_path, ink_a, srgb=False)
    return albedo_path, ink_path


def _save(path, arr, srgb=True):
    h, w = arr.shape[:2]
    if arr.ndim == 2:
        rgba = np.dstack([arr, arr, arr, np.ones_like(arr)])
    else:
        rgba = np.dstack([arr, np.ones((h, w), np.float32)])
    name = os.path.basename(path)
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    if not srgb:
        img.colorspace_settings.name = "Non-Color"
    # numpy row 0 is top; Blender pixel row 0 is bottom
    img.pixels.foreach_set(np.ascontiguousarray(rgba[::-1]).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print(f"[1617] texture written {path}")
