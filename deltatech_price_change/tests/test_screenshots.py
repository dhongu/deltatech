# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Modificarea prețului de listă, PV și etichete" — generate în
# timpul testelor, în limba RO, pe compania „Demo Magazin SRL" în RON.
#
# Scenariul din fișă: cana 35,00 -> 37,00 -> 39,00 lei și termosul 79,00 -> 89,00 lei în aceeași zi;
# setul de lingurițe 24,00 -> 26,00 -> 24,00 lei (revenire, nu rămâne în jurnal). Etichetele se
# pozează doar dacă puntea `deltatech_price_change_label` e instalată.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_price_change,deltatech_price_change_label,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPriceChangeScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_price_change"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [(4, company.id)], "company_id": company.id})
        for xmlid in ("sales_team.group_sale_manager", "stock.group_stock_manager"):
            group = env.ref(xmlid)
            env.user.group_ids = [(4, group.id)]
            admin.group_ids = [(4, group.id)]
        env.flush_all()

        env.user.name = "Ioana Marin"
        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.warehouse.write({"name": "Magazin Centru", "code": "MAG"})
        cls.location = cls.warehouse.lot_stock_id
        tax = cls.company_data["default_tax_sale"]

        def product(name, code, price, cost, qty):
            tmpl = env["product.template"].create(
                {
                    "name": name,
                    "default_code": code,
                    "barcode": False,
                    "type": "consu",
                    "is_storable": True,
                    "list_price": price,
                    "standard_price": cost,
                    "taxes_id": [(6, 0, tax.ids)],
                    "company_id": company.id,
                }
            )
            env["stock.quant"]._update_available_quantity(tmpl.product_variant_id, cls.location, qty)
            return tmpl

        cls.cana = product("Cană ceramică 350 ml", "CAN-350", 35.0, 20.0, 40)
        cls.termos = product("Termos inox 0,5 l", "TRM-050", 79.0, 50.0, 15)
        cls.lingurite = product("Set lingurițe (6 buc.)", "LNG-006", 24.0, 12.0, 30)

        # doar scenariul fișei în jurnal (setup-ul comun schimbă și prețurile produselor lui)
        env["product.price.change.log"].search([]).unlink()

        # modificările din cursul zilei
        cls.cana.list_price = 37.0
        cls.cana.list_price = 39.0
        cls.termos.list_price = 89.0
        cls.lingurite.list_price = 26.0
        cls.lingurite.list_price = 24.0

        cls.change = env["product.price.change"].create(
            {
                "type": "log",
                "use_product_template": True,
                "warehouse_id": cls.warehouse.id,
                "location_id": cls.location.id,
            }
        )
        cls.act_change = env.ref("deltatech_price_change.action_deltatech_price_change").id
        cls.act_log = env.ref("deltatech_price_change.action_price_change_log").id
        cls.act_product = env.ref("sale.product_template_action").id

    def _change_form(self, name, **extra):
        shot = {
            "url": f"action={self.act_change}&id={self.change.id}&model=product.price.change&view_type=form",
            "name": name,
            "wait": ".o_form_view",
        }
        shot.update(extra)
        return shot

    def test_capture_fise(self):
        self.capture_screenshots(
            [
                {
                    "url": f"action={self.act_product}&id={self.cana.id}&model=product.template&view_type=form",
                    "name": "01_produs_istoric_pret.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='list_price']", "button[name='action_view_price_change_log']"],
                },
                {
                    "url": f"action={self.act_log}&view_type=list",
                    "name": "02_jurnal_modificari.png",
                    "wait": ".o_list_view",
                },
                self._change_form("03_document_nou.png", highlight="button[name='action_load_price_changes']"),
            ],
            hide_systray=True,
        )

        self.change.action_load_price_changes()
        self.capture_screenshots(
            [self._change_form("04_document_linii.png", highlight="button[name='action_confirm']")],
            hide_systray=True,
        )

        self.change.action_confirm()
        shots = [
            self._change_form("05_document_confirmat.png"),
            self.report_shot("deltatech_price_change.report_pricechange", self.change, "06_pv_modificare_pret.png"),
        ]
        if hasattr(self.change, "action_print_labels"):
            action = self.change.action_print_labels()
            wizard = self.env["product.product.label"].with_context(**action["context"]).create({})
            shots += [
                self._change_form(
                    "07_etichete_wizard.png",
                    click_btn="button[name='action_print_labels']",
                    wait_after=".modal .o_form_view",
                    highlight=".modal button[name='print_labels']",
                    eval="document.activeElement && document.activeElement.blur()",
                ),
                self.report_shot("deltatech_price_change_label.shelf_label", wizard, "08_etichete_pdf.png"),
            ]
        self.capture_screenshots(shots, hide_systray=True)
