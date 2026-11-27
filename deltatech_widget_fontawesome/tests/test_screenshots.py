# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturile fișei consultant „Widget FontAwesome": RO pentru fișă, EN pentru USAGE.md.
#
# Modulul nu are ecrane proprii, așa că testul pune widget-ul pe câmpul Icon al tipurilor de
# activitate (mail.activity.type, care păstrează clase Font Awesome precum fa-phone), prin două
# view-uri moștenite create doar în tranzacția testului, și adaugă un tip fără iconiță.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_widget_fontawesome,deltatech_doc_screenshots \
#       --test-tags=/deltatech_widget_fontawesome:TestFontAwesomeScreenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestFontAwesomeScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_widget_fontawesome"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        if "mail.activity.type" not in cls.env:
            # modulul depinde doar de `web`; exemplele folosesc tipurile de activitate din `mail`
            raise unittest.SkipTest("mail neinstalat: capturile folosesc mail.activity.type")
        cls.prepare_ro_company(name="Demo Pictograme SRL")
        env = cls.env
        icon_field = '<field name="icon" position="replace"><field name="icon" widget="fontawesome"/></field>'
        for parent in ("mail.mail_activity_type_view_tree", "mail.mail_activity_type_view_form"):
            env["ir.ui.view"].create(
                {
                    "name": f"fontawesome demo {parent}",
                    "type": "list" if parent.endswith("tree") else "form",
                    "model": "mail.activity.type",
                    "inherit_id": env.ref(parent).id,
                    "arch": f"<data>{icon_field}</data>",
                }
            )
        cls.call_type = env.ref("mail.mail_activity_data_call")
        cls.empty_type = env["mail.activity.type"].create({"name": "Customer visit", "icon": False})
        cls.empty_type.with_context(lang="ro_RO").name = "Vizită client"

    def _shots(self):
        act = self.env.ref("mail.mail_activity_type_action").id
        model = "mail.activity.type"
        return [
            # 1. lista tipurilor de activitate: coloana Icon arată pictogramele
            {
                "url": f"action={act}&view_type=list&debug=1",
                "name": "01_lista_tipuri_pictograme.png",
                "wait": ".o_list_view .o_field_fontawesome, .o_list_view i.fa",
                "highlight": "th[data-name='icon']",
                "settle": 1500,
            },
            # 2. formularul tipului „Apel": pictograma telefonului în locul textului fa-phone
            {
                "url": f"action={act}&id={self.call_type.id}&model={model}&view_type=form&debug=1",
                "name": "02_formular_pictograma.png",
                "wait": ".o_form_view",
                "highlight": ".o_wrap_label:has(label[for='icon_0'])",
                "settle": 1500,
            },
            # 3. tip de activitate fără pictogramă: câmpul gol, formularul se deschide fără eroare
            {
                "url": f"action={act}&id={self.empty_type.id}&model={model}&view_type=form&debug=1",
                "name": "03_formular_fara_pictograma.png",
                "wait": ".o_form_view",
                "highlight": ".o_wrap_label:has(label[for='icon_0'])",
                "settle": 1500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True, viewport=(1400, 900))

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, viewport=(1400, 900), lang="en_US")
