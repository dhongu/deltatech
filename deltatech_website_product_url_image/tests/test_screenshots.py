# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Imaginea produsului din URL" — generate în timpul testelor,
# în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: adresa imaginii scrisă în Nume fișier imagine, imaginea încărcată pe produs,
# o imagine suplimentară (Media eCommerce) încărcată din URL și produsul în magazin.
# Descărcarea imaginii e simulată: capturile nu ies din test.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_website_product_url_image,deltatech_doc_screenshots \
#       --test-tags=/deltatech_website_product_url_image:TestUrlImageScreenshots --stop-after-init
import base64
import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image, ImageDraw

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

MAIN_URL = "https://cdn.furnizor-demo.ro/imagini/lampa-led-10w.png"
DETAIL_URL = "https://cdn.furnizor-demo.ro/imagini/lampa-led-10w-detaliu.png"


def _demo_image(background, accent):
    """O imagine de produs simplă (o lampă stilizată), generată în test."""
    img = Image.new("RGB", (800, 800), background)
    draw = ImageDraw.Draw(img)
    draw.polygon([(250, 330), (550, 330), (470, 180), (330, 180)], fill=accent)
    draw.ellipse((330, 330, 470, 470), fill="#fff3b0", outline=accent, width=10)
    draw.rectangle((385, 470, 415, 640), fill="#555555")
    draw.rectangle((280, 640, 520, 680), fill="#555555")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


IMAGES = {
    MAIN_URL: _demo_image("#e9f1fb", "#2f6db5"),
    DETAIL_URL: _demo_image("#eef7ee", "#3c8d40"),
}

# scrie adresa în câmp ca un operator; cu ``change`` câmpul e confirmat și pornește încărcarea
TYPE_URL_JS = """() => {{
    const input = document.querySelector("{selector} input");
    input.value = "{url}";
    input.dispatchEvent(new Event("input", {{bubbles: true}}));
    {commit}
    input.style.minWidth = "32em";
}}"""
COMMIT_JS = 'input.dispatchEvent(new Event("change", {bubbles: true}));'


def _type_url(selector, url, commit=False):
    return TYPE_URL_JS.format(selector=selector, url=url, commit=COMMIT_JS if commit else "")


@tagged("-at_install", "post_install", "fise_screenshots")
class TestUrlImageScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_product_url_image"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        cls.website = cls.env["website"].get_current_website()
        # magazinul în română, cu engleza ca a doua limbă (capturile EN pentru USAGE.md)
        lang_ro = cls.env.ref("base.lang_ro")
        lang_en = cls.env.ref("base.lang_en")
        cls.website.write(
            {
                "name": "Magazin Demo Iluminat",
                "language_ids": [Command.set((lang_ro | lang_en).ids)],
                "default_lang_id": lang_ro.id,
            }
        )
        category = cls.env["product.public.category"].create({"name": "Iluminat"})
        category.update_field_translations("name", {"ro_RO": "Iluminat", "en_US": "Lighting"})
        cls.product = cls.env["product.template"].create(
            {
                "name": "Lampă de birou LED 10 W",
                "default_code": "LMP-LED10",
                "list_price": 129.0,
                "sale_ok": True,
                "is_published": True,
                "website_id": cls.website.id,
                "public_categ_ids": [Command.set(category.ids)],
            }
        )
        cls.product.update_field_translations(
            "name", {"ro_RO": "Lampă de birou LED 10 W", "en_US": "LED desk lamp 10 W"}
        )
        # imaginea suplimentară există deja în Media eCommerce, cu imaginea veche
        cls.extra_image = cls.env["product.image"].create(
            {
                "name": "LMP-LED10",
                "product_tmpl_id": cls.product.id,
                "image_1920": base64.b64encode(_demo_image("#f4f4f4", "#9e9e9e")),
            }
        )

    def _fetch(self, url):
        return IMAGES.get(url)

    def _shots_form(self):
        product_form = f"id={self.product.id}&model=product.template&view_type=form"
        sales_tab = {"ro_RO": "Vânzări", "en_US": "Sales"}
        field = "div[name='image_file_name']"
        return [
            # 1. adresa imaginii, scrisă în Nume fișier imagine (tabul Vânzări)
            {
                "url": product_form,
                "name": "01_adresa_imagine_produs.png",
                "wait": ".o_form_view",
                "click_tab": sales_tab,
                "eval": _type_url(field, MAIN_URL),
                "settle": 2000,
                "highlight": [field],
            },
            # 2. la ieșirea din câmp imaginea se încarcă, iar câmpul păstrează doar numele fișierului
            {
                "url": product_form,
                "name": "02_imagine_incarcata_produs.png",
                "wait": ".o_form_view",
                "click_tab": sales_tab,
                "eval": _type_url(field, MAIN_URL, commit=True),
                "eval_wait": 3000,
                "settle": 2000,
                "highlight": ["div.oe_avatar[name='image_1920']", field],
            },
            # 3. imaginea suplimentară din Media eCommerce, încărcată din adresa scrisă în nume
            {
                "url": f"id={self.extra_image.id}&model=product.image&view_type=form",
                "name": "03_imagine_suplimentara_url.png",
                "wait": ".o_form_view",
                "eval": _type_url("div[name='name']", DETAIL_URL, commit=True),
                "eval_wait": 3000,
                "settle": 2000,
                "highlight": ["div[name='name']", "div[name='image_1920']"],
            },
        ]

    def _shots_shop(self):
        return [
            # 4. produsul în magazin, cu imaginea încărcată din URL
            {
                "path": {"ro_RO": self.product.website_url, "en_US": f"/en{self.product.website_url}"},
                "name": "04_produs_magazin_imagine.png",
                "wait": "#product_detail",
                "settle": 2500,
                "highlight": ["#product_detail_main .o_wsale_product_images"],
            },
        ]

    def _capture(self, **kwargs):
        model = type(self.env["product.template"])
        with patch.object(model, "_fetch_public_image", lambda record, url: self._fetch(url)):
            self.capture_screenshots(self._shots_form(), viewport=(1920, 1100), hide_systray=True, **kwargs)
            # salvat: imaginea principală și cea suplimentară, ca în magazin
            self.product.image_file_name = MAIN_URL
            self.extra_image.name = DETAIL_URL
            self.env.flush_all()
            self.capture_screenshots(self._shots_shop(), viewport=(1920, 1100), hide_systray=True, **kwargs)

    def test_capture_fise(self):
        self._capture()

    def test_capture_usage(self):
        self._capture(lang="en_US")
