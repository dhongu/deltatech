# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

"""Măști de decupare fără model ML, doar cu Pillow.

- fundal uniform (fotografie de produs pe alb, pe gri de studio): fundalul e ce
  are culoarea marginilor și e legat de margine; accesoriile închise la culoare
  (o pâlnie neagră lângă flacon) rămân, deși un model ML le pierde des;
- curățarea insulelor: bucățile mici rămase pe lângă produs se elimină.

Conectivitatea se calculează pe o copie micșorată (latura ``WORK_SIDE``), ca
parcurgerea în Python să rămână sub o secundă; marginea fină a produsului vine
din imaginea la rezoluția întreagă.
"""

from PIL import Image, ImageChops, ImageFilter

# Image.Resampling apare abia în Pillow 9.1; Odoo 19 acceptă și 9.0.1
_RESAMPLE = getattr(Image, "Resampling", Image)

WORK_SIDE = 400
# ponderea pixelilor de pe margine care trebuie să aibă culoarea fundalului
UNIFORM_BORDER_SHARE = 0.9


def _max_channel_diff(rgb, color):
    """Imagine L: cât diferă fiecare pixel de ``color``, pe canalul cel mai depărtat."""
    red, green, blue = ImageChops.difference(rgb, Image.new("RGB", rgb.size, color)).split()
    return ImageChops.lighter(ImageChops.lighter(red, green), blue)


def _work_size(size):
    scale = min(1.0, WORK_SIDE / float(max(size)))
    return max(1, round(size[0] * scale)), max(1, round(size[1] * scale))


def _shrink_mask(mask, size):
    """Micșorează o mască 0/255: un bloc e „plin” dacă are măcar un pixel plin.

    Media pe bloc (BOX) urmată de prag > 0 nu pierde detaliile subțiri, cum ar fi
    tubul unei pâlnii, care la o micșorare obișnuită s-ar topi în fundal.
    """
    return mask.resize(size, _RESAMPLE.BOX).point(lambda v: 255 if v else 0)


def _neighbours(index, width, height, diagonal):
    x, y = index % width, index // width
    for dx, dy in (
        ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1))
        if diagonal
        else ((-1, 0), (1, 0), (0, -1), (0, 1))
    ):
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            yield ny * width + nx


def _components(mask):
    """Componentele 8-conexe ale pixelilor plini, ca liste de indici (cea mai mare prima)."""
    width, height = mask.size
    data = mask.tobytes()
    seen = bytearray(len(data))
    components = []
    for start, value in enumerate(data):
        if not value or seen[start]:
            continue
        seen[start] = 1
        stack, component = [start], []
        while stack:
            index = stack.pop()
            component.append(index)
            for other in _neighbours(index, width, height, True):
                if data[other] and not seen[other]:
                    seen[other] = 1
                    stack.append(other)
        components.append(component)
    components.sort(key=len, reverse=True)
    return components


def _outside(mask):
    """Pixelii goi legați de margine, 4-conex (fundalul nu trece printre diagonale)."""
    width, height = mask.size
    data = mask.tobytes()
    seen = bytearray(len(data))
    stack = [
        index
        for index in (
            [x for x in range(width)]
            + [(height - 1) * width + x for x in range(width)]
            + [y * width for y in range(height)]
            + [y * width + width - 1 for y in range(height)]
        )
        if not data[index]
    ]
    for index in stack:
        seen[index] = 1
    while stack:
        index = stack.pop()
        for other in _neighbours(index, width, height, False):
            if not data[other] and not seen[other]:
                seen[other] = 1
                stack.append(other)
    return seen


def _mask_from_indices(size, indices):
    data = bytearray(size[0] * size[1])
    for index in indices:
        data[index] = 255
    return Image.frombytes("L", size, bytes(data))


def _keep_large(components, min_island):
    """Componentele de cel puțin ``min_island`` procente din cea mai mare."""
    if not components:
        return []
    limit = len(components[0]) * min_island / 100.0
    return [component for component in components if len(component) >= limit]


def border_color(rgb, tolerance):
    """Culoarea fundalului când marginile imaginii o au aproape toate; altfel ``None``."""
    small = rgb.resize(_work_size(rgb.size), _RESAMPLE.BOX)
    width, height = small.size
    pixels = small.load()
    border = [pixels[x, y] for x in range(width) for y in {0, height - 1}]
    border += [pixels[x, y] for y in range(1, height - 1) for x in {0, width - 1}]
    color = tuple(sorted(pixel[channel] for pixel in border)[len(border) // 2] for channel in range(3))
    close = sum(1 for pixel in border if max(abs(pixel[c] - color[c]) for c in range(3)) <= tolerance)
    return color if close >= UNIFORM_BORDER_SHARE * len(border) else None


def uniform_alpha(rgb, color, tolerance, min_island):
    """Canalul alfa pentru un produs pe fundal uniform de culoarea ``color``.

    Fundalul este ce seamănă cu ``color`` *și* e legat de marginea imaginii, deci
    zonele albe din interiorul etichetei rămân opace. Pe conturul produsului
    alfa trece treptat de la 0 la 255, ca marginea să nu fie zimțată.

    :return: imagine L, sau ``None`` când nu rămâne niciun obiect.
    """
    diff = _max_channel_diff(rgb, color)
    full = diff.point(lambda v: 255 if v > tolerance else 0)
    size = _work_size(rgb.size)
    small = _shrink_mask(full, size)
    outside = _outside(small)
    inside = Image.frombytes("L", size, bytes(0 if value else 255 for value in outside))
    kept = _keep_large(_components(inside), min_island)
    if not kept:
        return None
    region = _mask_from_indices(size, (index for component in kept for index in component))
    # interiorul (micșorat cu un bloc) e opac; banda de contur ia alfa din diferența de culoare
    interior = region.filter(ImageFilter.MinFilter(3)).resize(rgb.size, _RESAMPLE.NEAREST)
    band = region.filter(ImageFilter.MaxFilter(3)).resize(rgb.size, _RESAMPLE.NEAREST)
    high = min(255, tolerance * 3)
    edge = diff.point(
        lambda v: 0 if v <= tolerance else 255 if v >= high else (v - tolerance) * 255 // max(1, high - tolerance)
    )
    return ImageChops.lighter(interior, ImageChops.darker(band, edge))


def drop_islands(alpha, min_island):
    """Elimină din ``alpha`` bucățile mai mici de ``min_island`` procente din obiectul principal.

    :return: ``(alpha curățat, câte bucăți s-au eliminat)``
    """
    size = _work_size(alpha.size)
    small = _shrink_mask(alpha.point(lambda v: 255 if v > 127 else 0), size)
    components = _components(small)
    kept = _keep_large(components, min_island)
    dropped = len(components) - len(kept)
    if not dropped:
        return alpha, 0
    region = _mask_from_indices(size, (index for component in kept for index in component))
    keep = region.filter(ImageFilter.MaxFilter(3)).resize(alpha.size, _RESAMPLE.NEAREST)
    return ImageChops.darker(alpha, keep), dropped


def lost_share(reference, alpha):
    """Ce parte din ``reference`` (masca după culoare) lipsește din ``alpha`` (masca modelului)."""
    size = _work_size(alpha.size)
    ref = _shrink_mask(reference.point(lambda v: 255 if v > 127 else 0), size)
    got = alpha.point(lambda v: 255 if v > 127 else 0).resize(size, _RESAMPLE.BOX)
    total = ref.histogram()[255]
    if not total:
        return 0.0
    missing = ImageChops.subtract(ref, got.point(lambda v: 255 if v > 127 else 0)).histogram()[255]
    return missing / float(total)
