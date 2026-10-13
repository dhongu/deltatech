# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Control al marjei pe comanda de vânzare" — generate în
# timpul testelor, în limba RO, pe compania „Demo Marjă SRL" în RON.
#
# Seedează politica „Doar avertisment" și o comandă vândută sub cost pe ambalaj
# (cost 3 lei/kg → 36 lei/Cutie 12 kg, vândut la 30 lei/cutie), ca să arate atât
# semnalul, cât și faptul că vânzarea NU e blocată.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_margin,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleMarginScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_margin"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Marjă SRL")
        company = cls.env.company
        env = cls.env
        env.ref("base.user_admin").write({"company_ids": [Command.link(company.id)], "company_id": company.id})

        # drepturi de vânzări pe utilizatorul testului (seedează) și pe admin (e cel
        # autentificat în browserul de capturi)
        sale_manager = env.ref("sales_team.group_sale_manager", raise_if_not_found=False)
        if sale_manager:
            env.user.group_ids = [Command.link(sale_manager.id)]
            env.ref("base.user_admin").group_ids = [Command.link(sale_manager.id)]
        # „Unități de măsură": fără grupul ăsta coloana unității nu apare deloc în
        # captură, iar vânzarea pe ambalaj — miezul exemplului — nu s-ar vedea
        env["res.config.settings"].create({"group_uom": True}).execute()
        env.user.group_ids |= env.ref("uom.group_uom")
        env.ref("base.user_admin").group_ids |= env.ref("uom.group_uom")
        env.flush_all()

        # politica pusă pe „Doar avertisment": implicitul e „Blochează vânzarea", pe
        # care nu îl putem ilustra cu o captură (blocajul e un dialog de eroare)
        company.sale_margin_check_mode = "warn"
        env["ir.config_parameter"].sudo().set_param("sale.margin_limit", "0")
        env["ir.config_parameter"].sudo().set_param("sale.margin_limit_check_validate", "0")

        cls.partner = env["res.partner"].create({"name": "Lanț Retail SRL", "country_id": env.ref("base.ro").id})
        cls.partner.property_product_pricelist.name = "Listă de prețuri clienți RON"

        cls.uom_kg = env.ref("uom.product_uom_kgm")
        cls.uom_box = env["uom.uom"].create(
            {"name": "Cutie 12 kg", "relative_factor": 12.0, "relative_uom_id": cls.uom_kg.id}
        )
        # costul stă pe kg, vânzarea se face pe cutie: 3 lei/kg = 36 lei/cutie
        cls.product = env["product.product"].create(
            {
                "name": "Mere Idared calibru 70+",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.uom_kg.id,
                "standard_price": 3.0,
                "list_price": 3.5,
            }
        )
        # 30 lei/cutie e SUB costul convertit de 36 lei/cutie. O comparație
        # neconvertită (30 față de 3 lei/kg) ar arăta o marjă de 90% și ar rata
        # exact vânzările în ambalaje.
        cls.order = env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "product_uom_id": cls.uom_box.id,
                            "price_unit": 30.0,
                        }
                    )
                ],
            }
        )
        # a doua comandă, confirmată: dovedește în seed-ul capturilor că
        # `action_confirm` trece pe modul „warn" (pe „block" ar fi aruncat).
        # Nota din chatter NU are captură proprie: chatterul cade în mod
        # constant în afara cadrului capturat, iar nota e un efect al
        # confirmării, nu un ecran separat — e descrisă în pasul 2 al fișei.
        cls.order_confirmed = cls.order.copy()
        cls.order_confirmed.action_confirm()
        cls.settings_action = env.ref("sale.action_sale_config_settings")

    def test_capture_fise(self):
        self.capture_screenshots(
            [
                # 1. Politica și pragul, în Setări → Vânzări → Prețuri
                {
                    "url": f"action={self.settings_action.id}",
                    "name": "01_setari_politica.png",
                    "wait": ".o_form_view",
                    "settle": 3000,
                    "full": True,
                    "highlight": ["div[name='sale_margin_check_mode']"],
                },
                # 2. Semnalul pe comandă: bannerul + rândul marcat, cu Confirmă activ
                {
                    "url": f"id={self.order.id}&model=sale.order&view_type=form",
                    "name": "02_comanda_sub_cost.png",
                    "wait": ".o_form_view",
                    "settle": 2500,
                    "full": True,
                    "highlight": [".alert-warning", "div[name='order_line']"],
                },
            ]
        )
