# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Imaginile de produs — fundal eliminat, duplicate
# șterse, spațiu recuperat" — generate în timpul testelor, cu interfața în RO.
#
# Fotografiile de produs sunt desenate aici, iar modelul AI (rembg) e simulat: păstrează doar
# flaconul, ca un model real care pierde pâlnia de lângă el. Așa capturile ies la fel la fiecare
# rulare și nu au nevoie de rembg instalat.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_image_optimize,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_image_optimize:TestImageOptimizeScreenshots --stop-after-init
import base64
import io
import json
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFilter

from odoo.tests import tagged

from odoo.addons.deltatech_image_optimize.models import image_background, ir_attachment

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

SIZE = 1200
BOTTLE = (560, 200, 900, 1100)
CAP = (620, 120, 840, 200)
WIZARD_VIEWPORT = (1920, 1400)
# tabla de șah pusă sub imaginea transparentă, ca în coloana „After" a asistentului
CHECKER_JS = (
    "document.querySelectorAll(%s).forEach(img => {"
    "img.style.backgroundColor = '#fff';"
    "img.style.backgroundImage = 'conic-gradient(#d0d0d0 25%%, #fff 0 50%%, #d0d0d0 0 75%%, #fff 0)';"
    "img.style.backgroundSize = '16px 16px';})"
)


def _jpeg(img):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue())


def _bottle(draw, color, label):
    draw.rounded_rectangle(BOTTLE, 40, fill=color)
    draw.rectangle(CAP, fill=(30, 30, 30))
    draw.rectangle((600, 450, 860, 620), fill=label)
    draw.rectangle((600, 680, 860, 840), fill=(255, 255, 255))
    draw.rectangle((640, 720, 820, 800), fill=(70, 70, 70))


def _photo(background="white", funnel=False, specks=(), label=(25, 35, 130)):
    if background == "white":
        img = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    else:
        # fundal neuniform: un preș cu dungi și textură, ca pozele făcute în magazin
        img = Image.new("RGB", (SIZE, SIZE), (120, 160, 90))
        mat = ImageDraw.Draw(img)
        for x in range(0, SIZE, 60):
            mat.rectangle((x, 0, x + 30, SIZE), fill=(200, 210, 80))
        img = img.filter(ImageFilter.GaussianBlur(6))
    draw = ImageDraw.Draw(img)
    _bottle(draw, (236, 216, 40), label)
    if funnel:
        draw.ellipse((230, 210, 470, 290), fill=(20, 20, 20))
        draw.polygon([(300, 290), (400, 290), (368, 720), (332, 720)], fill=(28, 28, 28))
    for x, y in specks:
        draw.rectangle((x, y, x + 6, y + 6), fill=(60, 60, 60))
    return _jpeg(img)


def _fake_cutout(img, model_name):
    """Modelul AI simulat: păstrează doar flaconul (pierde accesoriile de lângă el)."""
    alpha = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.rounded_rectangle(BOTTLE, 40, fill=255)
    draw.rectangle(CAP, fill=255)
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


@tagged("-at_install", "post_install", "fise_screenshots")
class TestImageOptimizeScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_image_optimize"

    @classmethod
    def setUpClass(cls):
        # tooling-ul de capturi (l10n_ro_doc_screenshots) poate lipsi de pe disc (alt repo)
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil; capturile fișei se sar")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Catalog SRL")
        env = cls.env
        # capturile folosesc limita implicită de previzualizare (bg_sync_limit = 5 imagini)
        cls._set_param("bg_sync_limit", "5")

        Product = env["product.template"]
        cls.injector = Product.create(
            {
                "name": "Aditiv curățare injectoare diesel 300ml",
                "default_code": "AD-300-INJ",
                "image_1920": _photo(funnel=True, specks=[(150, 900)]),
                "is_published": True,
            }
        )
        cls.oil = Product.create(
            {
                "name": "Tratament ulei motor 300ml",
                "default_code": "AD-300-ULE",
                "image_1920": _photo(label=(150, 25, 25)),
                "is_published": True,
            }
        )
        cls.diesel = Product.create(
            {
                "name": "Aditiv motorină 1L",
                "default_code": "AD-1000-MOT",
                "image_1920": _photo(background="mat", label=(20, 110, 60)),
                "is_published": True,
            }
        )
        products = cls.injector | cls.oil | cls.diesel

        # galeria: aceeași poză de două ori pe un produs (duplicat de șters) și o poză comună
        # pe două produse (raportată, dar păstrată)
        repeated = _photo(label=(150, 25, 25), specks=[(1000, 1100)])
        shared = _photo(label=(90, 90, 90))
        Image_ = env["product.image"]
        for vals in (
            {"name": cls.oil.name, "product_tmpl_id": cls.oil.id, "image_1920": repeated},
            {"name": cls.oil.name, "product_tmpl_id": cls.oil.id, "image_1920": repeated},
            {"name": "Etichetă gamă aditivi", "product_tmpl_id": cls.injector.id, "image_1920": shared},
            {"name": "Etichetă gamă aditivi", "product_tmpl_id": cls.diesel.id, "image_1920": shared},
        ):
            Image_.create(vals)

        # lista produselor din capturi, fără produsele altor module
        cls.products_action = env["ir.actions.act_window"].create(
            {
                "name": "Produse",
                "res_model": "product.template",
                "view_mode": "list,form",
                "domain": [("id", "in", products.ids)],
            }
        )
        cls.params_action = env["ir.actions.act_window"].create(
            {
                "name": "Parametri de sistem",
                "res_model": "ir.config_parameter",
                "view_mode": "list,form",
                "domain": [("key", "=like", "deltatech_image_optimize.bg%")],
            }
        )
        env.flush_all()

    @classmethod
    def _set_param(cls, key, value):
        cls.env["ir.config_parameter"].sudo().set_param(f"deltatech_image_optimize.{key}", value)

    def _patch_rembg(self):
        """rembg „instalat", cu modelul simulat."""
        for target in (
            patch.object(ir_attachment, "_rembg_available", lambda: True),
            patch.object(image_background, "_rembg_available", lambda: True),
            patch.object(ir_attachment, "_rembg_cutout", _fake_cutout),
        ):
            self.startPatcher(target)

    @staticmethod
    def _open_action_js(names, open_wizard=True):
        """Bifează produsele, deschide meniul Acțiuni și, opțional, pornește acțiunea."""
        return f"""(async () => {{
            const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
            const names = {json.dumps(names)};
            const waitFor = async (test) => {{
                for (let i = 0; i < 40 && !test(); i++) {{
                    await sleep(250);
                }}
            }};
            // venind din alt ecran, lista se randează după ce selectorul de așteptare a apărut
            await waitFor(() => document.querySelectorAll('.o_data_row').length >= names.length);
            for (const row of document.querySelectorAll('.o_data_row')) {{
                if (names.some((n) => row.innerText.includes(n))) {{
                    row.querySelector('.o_list_record_selector input').click();
                    await sleep(200);
                }}
            }}
            await waitFor(() => document.querySelector('.o_cp_action_menus .dropdown-toggle'));
            await sleep(400);
            document.querySelector('.o_cp_action_menus .dropdown-toggle').click();
            await sleep(600);
            if ({json.dumps(open_wizard)}) {{
                [...document.querySelectorAll('.o-dropdown-item, .dropdown-item')]
                    .find((e) => e.innerText.includes('Remove Image Background')).click();
                await waitFor(() => document.querySelector('.modal .o_form_view'));
                await sleep(800);
            }}
        }})()"""

    def _products_shot(self, name, names, open_wizard=True, **kw):
        shot = {
            "url": f"action={self.products_action.id}&view_type=list",
            "name": name,
            "wait": ".o_list_view",
            "eval": self._open_action_js(names, open_wizard),
            "eval_wait": 1500,
            "settle": 1500,
        }
        if open_wizard:
            shot["eval"] += ".then(() => " + CHECKER_JS % json.dumps(".o_dt_bg_checker img") + ")"
        shot.update(kw)
        return shot

    def test_capture_fise(self):
        self._patch_rembg()
        all_names = [self.injector.name, self.oil.name, self.diesel.name]
        # 4 imagini (2 principale + 2 din galerie): încap în limita de previzualizare
        preview_names = [self.injector.name, self.diesel.name]

        # Pasul 1 — acțiunea pe lista de produse; Pasul 2 — previzualizarea, metoda automată
        self.capture_screenshots(
            [
                self._products_shot(
                    "01_produse_actiune.png",
                    all_names,
                    open_wizard=False,
                    highlight=[".o-dropdown-item:has-text('Remove Image Background')"],
                ),
                self._products_shot("02_previzualizare_automat.png", preview_names, full=True),
            ],
            viewport=WIZARD_VIEWPORT,
        )

        # Pasul 3 — modelul AI pierde pâlnia: rândul e semnalat și debifat
        self._set_param("bg_method", "rembg")
        self.env.flush_all()
        self.capture_screenshots(
            [
                self._products_shot(
                    "03_avertisment_model_ai.png",
                    [self.injector.name],
                    full=True,
                    highlight=["button[name='action_refresh']", ".modal td[name='warning']"],
                ),
            ],
            viewport=WIZARD_VIEWPORT,
        )

        # Pasul 4 — rezultatul aplicat pe produs (metoda automată)
        self._set_param("bg_method", "auto")
        action = self.injector.action_dt_remove_background()
        wizard = self.env[action["res_model"]].browse(action["res_id"])
        # doar imaginea principală: poza din galerie rămâne comună cu alt produs (Pasul 6)
        wizard.line_ids.filtered(lambda line: line.res_model == "product.image").to_apply = False
        wizard.action_apply()
        self.env.flush_all()

        dedup_action = self.env.ref("deltatech_image_optimize.action_product_image_dedup")
        cron = self.env.ref("deltatech_image_optimize.ir_cron_dt_image_optimize")
        self.capture_screenshots(
            [
                {
                    "url": f"action={self.products_action.id}&id={self.injector.id}"
                    "&model=product.template&view_type=form",
                    "name": "04_produs_dupa.png",
                    "wait": ".o_form_view",
                    # doar antetul cu imaginea; tab-urile produsului (prețuri, taxe) nu țin de pas
                    "eval": CHECKER_JS % json.dumps("div[name='image_1920'] img")
                    + "; document.querySelector('.o_form_sheet .o_notebook')?.remove()",
                    "highlight": ["div[name='image_1920']"],
                    "settle": 2000,
                },
                # Pasul 5 — toate cele 3 produse: 7 imagini, peste limită, deci coada
                self._products_shot("05_coada.png", all_names, highlight=[".modal button:has-text('Queue')"]),
                {
                    "url": f"action={self.params_action.id}&view_type=list",
                    "name": "06_parametri_sistem.png",
                    "wait": ".o_list_view",
                },
                {
                    "url": f"action={self.env.ref('deltatech_image_optimize.action_product_image_duplicate').id}"
                    "&view_type=list",
                    "name": "07_imagini_duplicate.png",
                    "wait": ".o_list_view",
                    # fără filtrul implicit „Removable", ca să se vadă și poza comună mai multor produse
                    "eval": "document.querySelector('.o_searchview_facet .o_facet_remove')?.click()",
                    "eval_wait": 1500,
                    "highlight": ["td[name='removable_count']"],
                },
                {
                    "url": f"action={dedup_action.id}",
                    "name": "08_eliminare_duplicate.png",
                    "wait": ".modal .o_form_view",
                    "highlight": ["button[name='action_apply']"],
                    "settle": 2000,
                },
                {
                    "url": f"id={cron.id}&model=ir.cron&view_type=form",
                    "name": "09_recomprimare_cron.png",
                    "wait": ".o_form_view",
                    "highlight": ["button[name='method_direct_trigger']", "div[name='active']"],
                },
            ],
            viewport=WIZARD_VIEWPORT,
        )
