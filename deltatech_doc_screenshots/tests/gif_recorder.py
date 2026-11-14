# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Înregistrează un GIF animat (demo de modul pentru Apps Store) dintr-o pagină Playwright.

Independent de Odoo: primește o pagină Playwright deja autentificată și produce cadrele pe măsură
ce scenariul acționează pagina. ``ScreenshotCase.capture_gif`` îl folosește pe un server de test;
poate fi folosit și direct, pe orice pagină.

Ce apare în GIF, peste interfață:
  - un **cursor simulat** (săgeată) care se deplasează lin spre fiecare țintă, cu un cerc la click;
  - o **subtitrare**, ca la film: text alb centrat jos, pe o bandă închisă semitransparentă care
    urmează rândurile textului (se rupe pe două rânduri dacă e lung);
  - opțional, un **slide de deschidere** (iconița modulului, titlu, rezumat, funcții), cu tranziție
    în fondu-nlănțuit spre primul ecran al fluxului.

Timpul din GIF e **virtual**: fiecare cadru primește o durată fixă (nu cât a durat captura), deci
animațiile au același ritm indiferent cât de rapid răspunde serverul. Cadrele identice consecutive
se comasează (durata se adună), iar GIF-ul folosește o paletă globală de 256 de culori, fără
dithering (interfața Odoo are culori plate; dithering-ul ar adăuga zgomot și mărime).
"""

import base64
import hashlib
import io
import math
import re
from html import escape

#: paleta Terrabit (aceeași ca bannerul de Apps Store)
GREEN_DARK = "#006F42"
GREEN_LIGHT = "#57B952"
GREEN_TITLE = "#00592F"
PILL_BG = "#E6F4EA"
TEXT_SUB = "#5F6B7A"
TEXT_FEAT = "#2F3A45"

_OVERLAY_CSS = """
#tbgif-cursor {
    position: fixed; left: 0; top: 0; width: 26px; height: 32px; z-index: 2147483647;
    pointer-events: none; filter: drop-shadow(0 2px 2px rgba(0,0,0,.35));
}
#tbgif-ripple {
    position: fixed; left: 0; top: 0; width: 0; height: 0; border-radius: 50%; z-index: 2147483646;
    pointer-events: none; background: rgba(87,185,82,.28); border: 2px solid rgba(0,111,66,.65);
    display: none;
}
#tbgif-caption {
    position: fixed; left: 8%; right: 8%; bottom: 30px; z-index: 2147483645; display: none;
    pointer-events: none; text-align: center;
    font: 500 23px/1.55 "Helvetica Neue", Helvetica, Arial, sans-serif; color: #fff;
}
#tbgif-caption span {
    /* banda urmează fiecare rând, ca subtitrările de film/TV */
    background: rgba(0,0,0,.78); padding: 3px 12px; border-radius: 3px;
    -webkit-box-decoration-break: clone; box-decoration-break: clone;
    text-shadow: 0 1px 2px rgba(0,0,0,.6);
}
"""

#: săgeata cursorului (alb cu contur negru, ca cea de sistem)
_CURSOR_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="32" viewBox="0 0 13 16">'
    '<path d="M1 1 L1 13.2 L4 10.4 L6.1 15 L8 14.2 L6 9.7 L10.2 9.7 Z" fill="#111" stroke="#fff" '
    'stroke-width="1" stroke-linejoin="round"/></svg>'
)

#: creează (o singură dată per document) cursorul, cercul de click și eticheta, apoi aplică starea
_OVERLAY_JS = """
(st) => {
    if (!document.body) { return; }
    let cursor = document.getElementById('tbgif-cursor');
    if (!cursor) {
        const style = document.createElement('style');
        style.id = 'tbgif-style';
        style.textContent = st.css;
        document.head.appendChild(style);
        cursor = document.createElement('div');
        cursor.id = 'tbgif-cursor';
        cursor.innerHTML = st.svg;
        const ripple = document.createElement('div');
        ripple.id = 'tbgif-ripple';
        const cap = document.createElement('div');
        cap.id = 'tbgif-caption';
        cap.innerHTML = '<span></span>';
        document.body.append(ripple, cap, cursor);
    }
    cursor.style.display = st.cursor ? 'block' : 'none';
    cursor.style.transform = `translate(${st.x - 2}px, ${st.y - 2}px)`;
    const ripple = document.getElementById('tbgif-ripple');
    if (st.ripple) {
        const r = st.ripple.r;
        ripple.style.display = 'block';
        ripple.style.width = ripple.style.height = `${2 * r}px`;
        ripple.style.transform = `translate(${st.x - r}px, ${st.y - r}px)`;
        ripple.style.opacity = st.ripple.o;
    } else {
        ripple.style.display = 'none';
    }
    const cap = document.getElementById('tbgif-caption');
    if (st.caption) {
        cap.firstChild.textContent = st.caption;
        cap.style.display = 'block';
    } else {
        cap.style.display = 'none';
    }
}
"""


def _ease(t):
    """Accelerare-decelerare (ease-in-out cubic) pentru deplasarea cursorului."""
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def intro_html(title, summary="", features=(), icon_png=None, eyebrow="", width=1120, height=700):
    """HTML-ul slide-ului de deschidere, în stilul bannerului Terrabit de Apps Store.

    ``icon_png`` sunt octeții iconiței modulului (``static/description/icon.png``); fără ea,
    partea dreaptă rămâne doar cu cercurile decorative.
    """
    icon = ""
    if icon_png:
        data = base64.b64encode(icon_png).decode()
        icon = f'<img class="icon" src="data:image/png;base64,{data}"/>'
    pills = "".join(f'<span class="pill"><i></i>{escape(f)}</span>' for f in features or ())
    s = width / 1120  # toate dimensiunile sunt gândite la 1120 px și scalate
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html, body {{ margin: 0; width: {width}px; height: {height}px; overflow: hidden; }}
body {{
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: {TEXT_FEAT};
    background: radial-gradient(circle at 82% 45%, #dff3e2 0, #f3faf4 38%, #fbfdfb 70%);
}}
.band {{ position: absolute; left: 0; top: 0; bottom: 0; width: {10 * s}px;
         background: linear-gradient({GREEN_LIGHT}, {GREEN_DARK}); }}
.left {{ position: absolute; left: {80 * s}px; top: 0; bottom: 0; width: {600 * s}px;
         display: flex; flex-direction: column; justify-content: center; }}
.eyebrow {{ display: flex; align-items: center; gap: {12 * s}px; color: {GREEN_DARK};
            font-weight: 700; letter-spacing: {2.4 * s}px; font-size: {15 * s}px; text-transform: uppercase; }}
.eyebrow:before {{ content: ""; width: {40 * s}px; height: {2 * s}px; background: {GREEN_LIGHT}; }}
h1 {{ margin: {18 * s}px 0 {18 * s}px; font-size: {50 * s}px; line-height: 1.08; color: {GREEN_TITLE};
      font-weight: 800; letter-spacing: -{0.5 * s}px; }}
.summary {{ font-size: {21 * s}px; line-height: 1.45; color: {TEXT_SUB}; }}
.pills {{ display: flex; flex-wrap: wrap; gap: {10 * s}px; margin-top: {38 * s}px; }}
.pill {{ display: inline-flex; align-items: center; gap: {9 * s}px; padding: {9 * s}px {16 * s}px;
         border-radius: 999px; background: #fff; border: 1px solid #d7e9db; font-size: {16 * s}px;
         font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
.pill i {{ width: {9 * s}px; height: {9 * s}px; border-radius: 50%; background: {GREEN_LIGHT}; }}
.ring {{ position: absolute; border-radius: 50%; border: {2 * s}px solid rgba(87,185,82,.35); }}
.card {{ position: absolute; left: {800 * s}px; top: 50%; width: {250 * s}px; height: {250 * s}px;
         transform: translate(-50%, -50%); border-radius: {44 * s}px; background: #fff;
         box-shadow: 0 {24 * s}px {60 * s}px rgba(0,89,47,.18); display: flex;
         align-items: center; justify-content: center; }}
.icon {{ width: {190 * s}px; height: {190 * s}px; border-radius: {24 * s}px; }}
</style></head><body>
<div class="band"></div>
<div class="ring" style="left:{575 * s}px;top:{height / 2 - 225 * s}px;width:{450 * s}px;height:{450 * s}px"></div>
<div class="ring" style="left:{640 * s}px;top:{height / 2 - 160 * s}px;width:{320 * s}px;height:{320 * s}px;
     border-style:dashed"></div>
<div class="card">{icon}</div>
<div class="left">
  <div class="eyebrow">{escape(eyebrow)}</div>
  <h1>{escape(title)}</h1>
  <div class="summary">{escape(summary)}</div>
  <div class="pills">{pills}</div>
</div>
</body></html>"""


class GifRecorder:
    """Scenariu → cadre → GIF. Toate duratele sunt în milisecunde de GIF (timp virtual)."""

    #: înălțimea (px) de jos rezervată subtitrării: o țintă care ar intra aici se derulează la mijloc
    SUBTITLE_ZONE = 170

    def __init__(self, page, fps=12, char_ms=70, move_ms=650, settle_ms=400, timeout=20000):
        self.page = page
        self.frame_ms = max(20, round(1000 / fps))
        self.char_ms = char_ms
        self.move_ms = move_ms
        self.settle_ms = settle_ms
        self.timeout = timeout
        vp = page.viewport_size or {"width": 1120, "height": 700}
        # cursorul pornește din centrul ecranului, ascuns până la prima mișcare
        self.x, self.y = vp["width"] / 2, vp["height"] * 0.55
        self.show_cursor = False
        self.caption_text = None
        self._ripple = None
        #: cadre: {"hash", "png", "ms", "fade"}; ``fade`` = tranziție în fondu-nlănțuit spre cadru
        self.frames = []
        self._fade_next = False

    # ---------------------------------------------------------------- stare și cadre
    def _apply_overlay(self):
        try:
            self.page.evaluate(
                _OVERLAY_JS,
                {
                    "css": _OVERLAY_CSS,
                    "svg": _CURSOR_SVG,
                    "cursor": self.show_cursor,
                    "x": self.x,
                    "y": self.y,
                    "ripple": self._ripple,
                    "caption": self.caption_text,
                },
            )
        except Exception:  # noqa: BLE001 - pagina în navigare: cadrul următor reîncearcă
            return

    def frame(self, ms=None):
        """Adaugă cadrul curent (cu durata ``ms``); un cadru identic cu precedentul doar o prelungește."""
        self._apply_overlay()
        png = self.page.screenshot(type="png")
        self.add_png(png, ms or self.frame_ms)

    def add_png(self, png, ms, fade=False):
        """Adaugă un cadru gata făcut (ex. slide-ul de deschidere)."""
        digest = hashlib.sha1(png).digest()
        fade = fade or self._fade_next
        self._fade_next = False
        if self.frames and self.frames[-1]["hash"] == digest and not fade:
            self.frames[-1]["ms"] += ms
            return
        self.frames.append({"hash": digest, "png": png, "ms": ms, "fade": fade})

    def fade_next(self):
        """Următorul cadru intră printr-o tranziție în fondu-nlănțuit (ex. după slide-ul de deschidere)."""
        self._fade_next = True

    def settle(self, ms=None):
        """Așteaptă (în timp real) să se termine cererile și re-randarea, fără a adăuga cadre."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=2000)
        except Exception:  # noqa: BLE001 - long-polling (bus) ține rețeaua ocupată: pauză fixă
            self.page.wait_for_timeout(250)
        self.page.wait_for_timeout(self.settle_ms if ms is None else ms)

    # ---------------------------------------------------------------- acțiuni
    def hold(self, ms):
        """Ține ecranul curent ``ms`` milisecunde în GIF."""
        self.frame(ms)

    def caption(self, text, hold=None):
        """Afișează subtitrarea (rămâne până la următoarea); ``text`` gol o ascunde."""
        self.caption_text = text or None
        self.frame(hold)

    def _target_point(self, selector):
        # doar elementele vizibile: formularele Odoo au des același ``name`` și în părți ascunse
        loc = self.page.locator(selector).locator("visible=true").first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.scroll_into_view_if_needed(timeout=self.timeout)
        box = loc.bounding_box()
        vh = (self.page.viewport_size or {"height": 700})["height"]
        if box and (box["y"] + box["height"] > vh - self.SUBTITLE_ZONE or box["y"] < 0):
            # ținta (și ce apare sub ea după acțiune: câmpuri completate, liniile noi) ar sta sub
            # subtitrare sau la margine: o aducem în mijlocul ecranului (Odoo derulează .o_content)
            loc.evaluate("el => el.scrollIntoView({block: 'center'})")
            self.page.wait_for_timeout(150)
            box = loc.bounding_box()
        if not box:
            raise AssertionError(f"Ținta '{selector}' nu are poziție pe ecran")
        # puțin spre stânga-centru, ca la un utilizator real (nu fix pe mijlocul unui câmp lung)
        x = box["x"] + min(box["width"] / 2, 60)
        return loc, x, box["y"] + box["height"] / 2

    def move(self, selector, ms=None):
        """Deplasează lin cursorul simulat (și pe cel real, pentru stările :hover) până la ``selector``."""
        loc, tx, ty = self._target_point(selector)
        self._glide(tx, ty, ms)
        return loc

    def _glide(self, tx, ty, ms=None):
        if not self.show_cursor:
            self.show_cursor = True
        dist = math.hypot(tx - self.x, ty - self.y)
        ms = ms or self.move_ms
        steps = max(1, min(round(ms / self.frame_ms), max(2, round(dist / 25))))
        sx, sy = self.x, self.y
        for i in range(1, steps + 1):
            t = _ease(i / steps)
            self.x, self.y = sx + (tx - sx) * t, sy + (ty - sy) * t
            self.frame(self.frame_ms)
        self.page.mouse.move(self.x, self.y)

    def click(self, selector, wait_after=None, hold=None):
        """Mută cursorul pe ``selector``, arată cercul de click, apasă și așteaptă ``wait_after``."""
        loc = self.move(selector)
        for r, o in ((10, 0.9), (17, 0.7), (24, 0.4)):
            self._ripple = {"r": r, "o": o}
            self.frame(self.frame_ms)
        self._ripple = None
        loc.click(timeout=self.timeout)
        if wait_after:
            self.page.wait_for_selector(wait_after, timeout=self.timeout)
        self.settle()
        self.frame(hold)

    def type(self, text, into=None, clear=False, hold=None):
        """Tastează ``text`` literă cu literă (opțional după click în câmpul ``into``).

        ``into`` e un selector sau, scurt, numele tehnic al unui câmp de formular Odoo (``"vat"``):
        atunci ținta e inputul/textarea-ul widgetului (``name`` e textarea pe partener în 19.0).
        """
        if into and re.fullmatch(r"\w+", into):
            into = f".o_field_widget[name='{into}'] :is(input, textarea, [contenteditable='true'])"
        if into:
            self.click(into)
        if clear:
            self.page.keyboard.press("ControlOrMeta+A")
            self.page.keyboard.press("Backspace")
        for ch in text:
            self.page.keyboard.type(ch)
            self.frame(self.char_ms)
        self.settle(150)
        self.frame(hold)

    def press(self, key, wait_after=None, hold=None):
        """Apasă o tastă (ex. ``Enter``, ``Tab``) și așteaptă reacția interfeței."""
        self.page.keyboard.press(key)
        if wait_after:
            self.page.wait_for_selector(wait_after, timeout=self.timeout)
        self.settle()
        self.frame(hold)

    def hide_cursor(self):
        self.show_cursor = False

    # ---------------------------------------------------------------- export
    def save(self, path, scale=1.0, fade_steps=5, colors=256):
        """Scrie GIF-ul (buclă infinită) și întoarce ``(număr_cadre, durată_ms)``."""
        from PIL import Image  # noqa: PLC0415

        if not self.frames:
            raise AssertionError("GIF fără cadre")
        # Pillow 9.0.1 (fixat de Odoo 19 pe Python 3.10) n-are enum-urile Image.Quantize/Dither/Resampling
        quantize = getattr(Image, "Quantize", Image)
        dither = getattr(Image, "Dither", Image)
        resample = getattr(Image, "Resampling", Image).LANCZOS

        def load(f):
            img = Image.open(io.BytesIO(f["png"])).convert("RGB")
            if scale != 1.0:
                img = img.resize((round(img.width * scale), round(img.height * scale)), resample)
            return img

        # Paleta globală: dintr-un mozaic de cadre eșantionate, la mărime reală (o micșorare ar
        # amesteca culorile), ca toate cadrele să aibă aceleași culori (fără pâlpâiri) și GIF-ul
        # să rămână mic. FASTOCTREE păstrează și culorile rare (linkuri, butoane, insigne):
        # MEDIANCUT le topește în nuanța vecină dominantă (teal → verde, mov → gri).
        sample = self.frames[:: max(1, len(self.frames) // 6)][:6]
        first = load(sample[0])
        tw, th = first.width, first.height
        mosaic = Image.new("RGB", (tw * 3, th * math.ceil(len(sample) / 3)), "white")
        for i, f in enumerate(sample):
            mosaic.paste(load(f), ((i % 3) * tw, (i // 3) * th))
        palette = mosaic.quantize(colors, method=quantize.FASTOCTREE, dither=dither.NONE)

        out, durations = [], []
        prev = None
        for f in self.frames:
            img = load(f)
            if f["fade"] and prev is not None and prev.size == img.size:
                for k in range(1, fade_steps + 1):
                    out.append(
                        Image.blend(prev, img, k / (fade_steps + 1)).quantize(palette=palette, dither=dither.NONE)
                    )
                    durations.append(self.frame_ms)
            out.append(img.quantize(palette=palette, dither=dither.NONE))
            durations.append(max(20, int(f["ms"])))
            prev = img
        out[0].save(path, save_all=True, append_images=out[1:], duration=durations, loop=0, optimize=False, disposal=1)
        return len(out), sum(durations)
