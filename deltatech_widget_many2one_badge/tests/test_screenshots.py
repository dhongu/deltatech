# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Eticheta colorată pentru câmpurile de tip listă de alegere":
# același ecran în RO (fișa) și în EN (USAGE.md).
#
# Modulul nu are ecrane proprii: widgetul se vede pe faza comenzii de vânzare din
# deltatech_sale_stage (listă și formular). Testul se sare dacă acel modul nu e instalat.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_widget_many2one_badge,deltatech_sale_stage,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots/deltatech_widget_many2one_badge --stop-after-init --without-demo=True
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# fazele demo: (nume EN, nume RO, culoare Odoo 0–11)
PHASES = [
    ("Order sent", "Ofertă transmisă", 4),
    ("Confirmed", "Confirmată", 8),
    ("Shipped", "Expediată", 2),
    ("Delivered", "Livrată", 10),
]


@tagged("-at_install", "post_install", "fise_screenshots")
class TestMany2oneBadgeScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_widget_many2one_badge"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        if "sale.order.phase" not in cls.env:
            raise unittest.SkipTest("deltatech_sale_stage nu e instalat: widgetul nu are unde fi arătat")
        cls.prepare_ro_company(name="Demo Etichete SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.group_ids = [Command.link(env.ref("sales_team.group_sale_manager").id)]

        cls.phases = env["sale.order.phase"]
        for sequence, (name_en, name_ro, color) in enumerate(PHASES, start=1):
            phase = env["sale.order.phase"].create({"name": name_en, "color": color, "sequence": sequence})
            phase.with_context(lang="ro_RO").name = name_ro
            cls.phases |= phase

        # lista de prețuri în moneda companiei (creată înainte, în USD)
        pricelists = env["product.pricelist"].search([])
        pricelists.write({"name": "RON price list", "currency_id": env.company.currency_id.id})
        pricelists.with_context(lang="ro_RO").name = "Listă de prețuri RON"
        product = env["product.product"].create(
            {"name": "Covorașe auto Dacia Duster", "list_price": 189.0, "taxes_id": [Command.clear()]}
        )
        customers = [
            "Auto Service Brașov SRL",
            "Ionescu Andrei",
            "Flota Rapid Transport SRL",
            "Popa Elena",
            "Moto Parts Cluj SRL",
            "Dumitrescu Mihai",
        ]
        cls.orders = env["sale.order"]
        for index, name in enumerate(customers):
            partner = env["res.partner"].create({"name": name, "country_id": env.ref("base.ro").id})
            order = env["sale.order"].create(
                {
                    "partner_id": partner.id,
                    "order_line": [Command.create({"product_id": product.id, "product_uom_qty": 1 + index})],
                }
            )
            order.action_confirm()
            order.phase_id = cls.phases[index % len(cls.phases)]
            cls.orders |= order
        cls.order = cls.orders[1]

    def _shots(self):
        action = self.env.ref("sale.action_orders")
        return [
            # 1. lista comenzilor, cu faza fiecărei comenzi ca etichetă colorată
            {
                "url": f"action={action.id}&model=sale.order&view_type=list",
                "name": "01_lista_comenzi_faze.png",
                "wait": ".o_list_view .o_tag",
                "highlight": [".o_data_row:nth-child(3) td[name='phase_id']"],
                "settle": 2000,
            },
            # 2. comanda deschisă: eticheta fazei, cu × pentru ștergere
            {
                "url": f"action={action.id}&id={self.order.id}&model=sale.order&view_type=form",
                "name": "02_comanda_eticheta_faza.png",
                "wait": ".o_form_view .o_field_many2one_badge .o_tag",
                "hover": ".o_field_many2one_badge .o_tag",
                "highlight": ["div[name='phase_id']"],
                "settle": 2000,
            },
            # 3. click pe etichetă: paleta de culori a fazei
            {
                "url": f"action={action.id}&id={self.order.id}&model=sale.order&view_type=form",
                "name": "03_alegere_culoare.png",
                "wait": ".o_form_view .o_field_many2one_badge .o_tag",
                "click_btn": ".o_field_many2one_badge .o_tag",
                "wait_after": ".o_tag_popover .o_colorlist",
                "highlight": [".o_tag_popover"],
                "settle": 2000,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")
