# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Câmp Markdown cu editare vizuală" (RO) și pentru
# readme/USAGE.md (EN).
#
# Modulul nu adaugă câmpuri sau ecrane: testul creează un formular de probă pe atașamente
# (ir.attachment), cu câmpul text Descriere afișat cu widget="markdown", o dată editabil și o dată
# doar în citire, și trei atașamente cu conținut Markdown.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_markdown_field,deltatech_doc_screenshots \
#       --test-tags=/deltatech_markdown_field:TestMarkdownFieldScreenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

NOTES = """# Procedură de recepție

Verificați **cantitatea** și *data de expirare* la fiecare palet.

- comparați avizul cu comanda;
- fotografiați ambalajul deteriorat;
- semnalați diferențele în [portalul furnizorului](https://www.terrabit.ro).

> Marfa refuzată rămâne în zona de carantină.
"""

OFFER = """## Condiții ofertă

1. **Palet A**: 10 bucăți, livrare în 5 zile;
2. **Palet B**: 4 bucăți, livrare în 10 zile.

Prețurile nu includ transportul.

`Valabilitate: 30 de zile`
"""

MIXED = """## Text cu HTML

Combinația <kbd>Ctrl</kbd> + <kbd>S</kbd> salvează, iar textul <mark>marcat</mark> rămâne vizibil.

<iframe src="https://www.terrabit.ro" width="600" height="200"></iframe>

Cadrul încorporat de mai sus nu se mai afișează.
"""

ARCH = """
<form>
    <sheet>
        <group>
            <field name="name"/>
        </group>
        <field name="description" widget="markdown" class="w-100" %s options="{'min_height': 220}"/>
    </sheet>
</form>
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestMarkdownFieldScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_markdown_field"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.activate_ro_lang()
        cls.force_light_theme()
        View = cls.env["ir.ui.view"]
        Action = cls.env["ir.actions.act_window"]
        cls.actions = {}
        for key, extra in (("edit", ""), ("read", 'readonly="1"')):
            view = View.create(
                {
                    "name": f"Demo Markdown {key}",
                    "model": "ir.attachment",
                    "type": "form",
                    "mode": "primary",
                    "priority": 99,
                    "arch": ARCH % extra,
                }
            )
            cls.actions[key] = Action.create(
                {
                    "name": "Demo Markdown",
                    "res_model": "ir.attachment",
                    "view_mode": "form",
                    "view_id": view.id,
                }
            )
        Attachment = cls.env["ir.attachment"]
        cls.notes = Attachment.create({"name": "Procedură recepție", "type": "url", "url": "#", "description": NOTES})
        cls.offer = Attachment.create({"name": "Condiții ofertă", "type": "url", "url": "#", "description": OFFER})
        cls.mixed = Attachment.create({"name": "Text cu HTML", "type": "url", "url": "#", "description": MIXED})

    def _url(self, key, rec):
        return f"action={self.actions[key].id}&id={rec.id}&model=ir.attachment&view_type=form"

    def _shots(self):
        return [
            {
                "url": self._url("edit", self.notes),
                "name": "01_editare_markdown.png",
                "wait": ".o_md_editor h1",
                "highlight": [".o_md_toolbar"],
            },
            {
                "url": self._url("read", self.offer),
                "name": "02_afisare_doar_citire.png",
                "wait": ".o_md_editor ol",
                "highlight": ["div[name='description']"],
            },
            {
                "url": self._url("read", self.mixed),
                "name": "03_html_filtrat.png",
                "wait": ".o_md_editor kbd",
                "highlight": ["div[name='description']"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US", hide_systray=True)
