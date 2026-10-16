# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

"""Eliminarea unui watermark semi-transparent care și-a lăsat urma în canalul alfa.

Unele programe de watermark amestecă sigla peste imagine și, în același timp, scad
transparența pixelilor din siglă. Imaginea salvată păstrează astfel, în canalul alfa,
masca exactă a siglei, chiar și peste produs: ``d = 255 - alfa`` arată cât de puternic
a fost amestecată sigla în fiecare pixel.

Amestecul se învață din imaginile catalogului, pentru fiecare treaptă ``d``::

    ieșire = original · (1 - t[d]) + q[d]          (q[d] = culoarea siglei · t[d])

și apoi se inversează. Pentru fiecare treaptă e nevoie de pixeli peste fundal deschis
și peste fundal închis, ca opacitatea să poată fi separată de culoare; treptele fără
destule date se interpolează din vecine.

numpy e o dependență opțională, importată doar aici (vine odată cu rembg).
"""

import io

from PIL import Image

# Image.Resampling apare abia în Pillow 9.1; Odoo 19 acceptă și 9.0.1
_RESAMPLE = getattr(Image, "Resampling", Image)

# urma unui watermark e o scădere mică a transparenței; sub acest prag e transparență reală
TRACE_MIN_ALPHA = 128
TRACE_MIN_SHARE = 0.002
TRACE_MAX_SHARE = 0.8
# rezoluția maximă la învățare: amestecul nu depinde de mărime, iar timpul scade mult
LEARN_SIDE = 1200
NEIGHBOUR_RADIUS = 8
FLAT_VARIANCE = 9.0
MIN_SAMPLES = 50
MIN_SPREAD = 80.0


def numpy_available():
    try:
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def load_rgba(raw):
    """Imaginea ca RGBA, sau ``None`` când nu are canal de transparență."""
    img = Image.open(io.BytesIO(raw))
    img.load()
    if img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
        return img.convert("RGBA")
    return None


def has_alpha_trace(img):
    """True când transparența imaginii arată ca urma unui watermark, nu ca un decupaj."""
    if img is None:
        return False
    alpha = img.getchannel("A")
    hist = alpha.histogram()
    total = img.width * img.height
    trace = sum(hist[TRACE_MIN_ALPHA:255])
    real = sum(hist[:TRACE_MIN_ALPHA])
    return TRACE_MIN_SHARE <= trace / total <= TRACE_MAX_SHARE and real / total < 0.01


def _blur(np, x, r):
    """Media pe o fereastră (2r+1)², cu sume cumulate."""
    pad = np.pad(x, r + 1, mode="edge")
    c = pad.cumsum(0).cumsum(1)
    k = 2 * r + 1
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return (s / (k * k))[: x.shape[0], : x.shape[1]]


def _neighbourhood(np, rgb, d, radius):
    """Fundalul estimat sub fiecare pixel, din vecinii fără siglă pe raza dată."""
    clean = (d == 0).astype(np.float64)
    weight = _blur(np, clean, radius)
    safe = np.maximum(weight, 1e-3)
    lum = rgb.mean(-1)
    mean = _blur(np, lum * clean, radius) / safe
    var = _blur(np, lum * lum * clean, radius) / safe - mean**2
    orig = np.stack([_blur(np, rgb[..., k] * clean, radius) / safe for k in range(3)], -1)
    # doar unde fundalul din jur e uniform și are destui vecini curați: acolo estimarea e sigură
    return orig, (weight > 0.3) & (var < FLAT_VARIANCE)


def _samples(np, img):
    """Pixelii din siglă și fundalul estimat sub ei.

    Raza mică urmărește bine fundalul lângă literele subțiri; în interiorul unei sigle
    pline nu are vecini curați, așa că acolo se folosește o rază mai mare.
    """
    if max(img.size) > LEARN_SIDE:
        img = img.copy()
        img.thumbnail((LEARN_SIDE, LEARN_SIDE), _RESAMPLE.BOX)
    arr = np.asarray(img, dtype=np.float64)
    rgb, d = arr[..., :3], 255 - arr[..., 3]
    orig, valid = _neighbourhood(np, rgb, d, NEIGHBOUR_RADIUS)
    wide, wide_valid = _neighbourhood(np, rgb, d, NEIGHBOUR_RADIUS * 3)
    use_wide = ~valid & wide_valid
    orig[use_wide] = wide[use_wide]
    mask = (d > 0) & (valid | wide_valid)
    return orig[mask], rgb[mask], d[mask]


def learn_alpha_trace(images):
    """Învață amestecul din imaginile cu urmă în alfa.

    :param images: imagini RGBA (``PIL.Image``)
    :return: ``{"t": [256], "q": [[r, g, b] x 256]}``, sau ``None`` când imaginile nu au
        destui pixeli de siglă peste fundaluri diferite
    """
    import numpy as np

    parts = [_samples(np, img) for img in images if has_alpha_trace(img)]
    if not parts:
        return None
    orig = np.concatenate([p[0] for p in parts])
    out = np.concatenate([p[1] for p in parts])
    d = np.concatenate([p[2] for p in parts])
    t = np.full(256, np.nan)
    q = np.full((256, 3), np.nan)
    for level in range(1, 256):
        sel = np.abs(d - level) <= 1
        if sel.sum() < MIN_SAMPLES or np.ptp(orig[sel].mean(1)) < MIN_SPREAD:
            continue
        o, y = orig[sel], out[sel]
        # y_c = o_c - t·o_c + q_c  ->  necunoscutele t, q_r, q_g, q_b
        a = np.zeros((len(o) * 3, 4))
        b = np.zeros(len(o) * 3)
        for k in range(3):
            a[k::3, 0] = -o[:, k]
            a[k::3, 1 + k] = 1
            b[k::3] = y[:, k] - o[:, k]
        sol = np.linalg.lstsq(a, b, rcond=None)[0]
        if 0 < sol[0] < 0.95:
            t[level], q[level] = sol[0], sol[1:]
    known = ~np.isnan(t)
    if not known.any():
        return None
    levels = np.arange(256)
    top = levels[known][-1]
    t_known, q_known = t[known], q[known]
    t = np.interp(levels, levels[known], t_known)
    q = np.stack([np.interp(levels, levels[known], q_known[:, k]) for k in range(3)], -1)
    # peste ultima treaptă cu date, amestecul crește proporțional cu scăderea transparenței
    above = levels > top
    t[above] = np.minimum(t_known[-1] * levels[above] / top, 0.95)
    q[above] = q_known[-1] * (levels[above] / top)[:, None]
    t[0], q[0] = 0.0, 0.0
    return {"t": t.round(5).tolist(), "q": q.round(3).tolist()}


def remove_alpha_trace(img, model):
    """Imaginea fără watermark, opacă (RGB): scăderea transparenței era chiar sigla."""
    import numpy as np

    arr = np.asarray(img, dtype=np.float64)
    rgb = arr[..., :3]
    d = (255 - arr[..., 3]).astype(int)
    t = np.asarray(model["t"])
    q = np.asarray(model["q"])
    out = (rgb - q[d]) / (1 - t[d])[..., None]
    return Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8), "RGB")


def trace_preview(img):
    """Masca siglei, întunecată pe alb, ca să se vadă ce a găsit asistentul."""
    alpha = img.getchannel("A")
    low = min(alpha.getextrema()[0], 254)
    scale = 255.0 / (255 - low)
    return alpha.point(lambda v: 255 - min(255, int((255 - v) * scale))).convert("RGB")
