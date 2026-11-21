# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Facturare automată din transferuri", în RO (fișa) și EN
# (readme/USAGE.md), pe planul de conturi românesc (`setup_country("ro")`).
#
# Seed: tipul Livrări facturează la validare și postează factura, tipul Recepții facturează
# programat. Livrarea comenzii S00101 (6 scaune) e facturată la validare; recepția comenzii
# P00101 (5 birouri) primește factura furnizorului în ciornă la rularea programată; recepția
# comenzii P00102 (3 birouri) e facturată manual din comandă înainte de rularea programată, deci
# facturarea ei automată eșuează cu motivul afișat pe transfer.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,deltatech_invoice_picking_automatically,deltatech_doc_screenshots \
#       --test-tags=/deltatech_invoice_picking_automatically:TestInvoicePickingAutomaticallyScreenshots \
#       --stop-after-init
import json
import unittest

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

ADDITIONAL_INFO = {"ro_RO": "Informații suplimentare", "en_US": "Additional Info"}

# Coloana „Facturare automată" e opțională și ascunsă implicit: o afișăm din meniul coloanelor.
SHOW_COLUMN = """
    new Promise((resolve) => {
        document.querySelector('.o_list_view .o_optional_columns_dropdown_toggle').click();
        setTimeout(() => {
            const input = [...document.querySelectorAll('.o-dropdown--menu input[type=checkbox]')]
                .find((i) => i.closest('.dropdown-item, label, span').textContent.includes('%(label)s'));
            if (input && !input.checked) input.click();
            document.body.click();
            setTimeout(resolve, 1000);
        }, 800);
    })
"""


def _do_action(action, context=None):
    """JS: deschide o acțiune (sau un xmlid de acțiune) în locul ecranului curent."""
    options = json.dumps({"clearBreadcrumbs": True, "additionalContext": context or {}})
    return f"odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(action)}, {options})"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestInvoicePickingAutomaticallyScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_invoice_picking_automatically"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        cls.prepare_ro_company(name="Demo Mobilier SRL")
        company = env.company
        groups = [
            env.ref(xmlid).id
            for xmlid in (
                "sales_team.group_sale_manager",
                "stock.group_stock_manager",
                "purchase.group_purchase_manager",
                "account.group_account_manager",
            )
        ]
        # utilizatorul testului face seed-ul, admin face capturile
        env.user.group_ids = [Command.link(group) for group in groups]
        env.ref("base.user_admin").write(
            {
                "company_ids": [Command.link(company.id)],
                "company_id": company.id,
                "name": "Maria Ionescu",
                "group_ids": [Command.link(group) for group in groups],
            }
        )

        tax_sale = env["account.tax"].search(
            [("type_tax_use", "=", "sale"), ("amount", "=", 21.0), ("company_id", "=", company.id)], limit=1
        )
        tax_purchase = env["account.tax"].search(
            [("type_tax_use", "=", "purchase"), ("amount", "=", 21.0), ("company_id", "=", company.id)], limit=1
        )
        product_vals = {
            "is_storable": True,
            "invoice_policy": "delivery",
            "purchase_method": "receive",
            "taxes_id": [Command.set(tax_sale.ids)],
            "supplier_taxes_id": [Command.set(tax_purchase.ids)],
        }
        cls.chair = env["product.product"].create(
            {"name": "Scaun ergonomic Nova", "list_price": 450.0, "standard_price": 300.0, **product_vals}
        )
        cls.desk = env["product.product"].create(
            {"name": "Birou reglabil Flex", "list_price": 1200.0, "standard_price": 800.0, **product_vals}
        )
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        # depozitul companiei de test are nume tehnic (company_1_data / compa)
        warehouse.write({"name": "Depozit central", "code": "DC"})
        cls.delivery_type = warehouse.out_type_id
        cls.receipt_type = warehouse.in_type_id
        for picking_type, names in (
            (cls.delivery_type, {"ro_RO": "Livrări", "en_US": "Delivery Orders"}),
            (cls.receipt_type, {"ro_RO": "Recepții", "en_US": "Receipts"}),
        ):
            picking_type.auto_batch = False
            for lang, name in names.items():
                picking_type.with_context(lang=lang).name = name
        cls.delivery_type.write(
            {"create_invoice_automatically": True, "invoice_moment": "validation", "post_invoice_automatically": True}
        )
        cls.receipt_type.write({"create_invoice_automatically": True, "invoice_moment": "cron"})
        # lista de prețuri de test din `product` are nume englezesc
        pricelist = env["product.pricelist"].search([("name", "=", "Test Pricelist")])
        pricelist.with_context(lang="en_US").name = "Standard pricelist"
        pricelist.with_context(lang="ro_RO").name = "Listă de prețuri standard"
        env["stock.quant"]._update_available_quantity(cls.chair, warehouse.lot_stock_id, 100.0)

        ro = env.ref("base.ro").id
        cls.alfa, cls.beta = env["res.partner"].create(
            [
                {"name": "Alfa Construct SRL", "country_id": ro, "lang": "ro_RO"},
                {"name": "Beta Mobila SRL", "country_id": ro, "lang": "ro_RO"},
            ]
        )

        # livrarea: facturată și postată chiar la validare
        cls.order = env["sale.order"].create(
            {
                "name": "S00101",
                "partner_id": cls.alfa.id,
                "user_id": env.ref("base.user_admin").id,
                "order_line": [Command.create({"product_id": cls.chair.id, "product_uom_qty": 6.0})],
            }
        )
        cls.order.action_confirm()
        cls.delivery = cls.order.picking_ids
        cls._validate(cls.delivery)
        cls.invoice = cls.delivery.account_move_id

        # recepția P00101: factura furnizorului vine la rularea programată, în ciornă
        cls.receipt = cls._purchase("P00101", 5.0).picking_ids
        cls._validate(cls.receipt)
        env["stock.picking"]._cron_generate_invoices()
        cls.bill = cls.receipt.account_move_id

        # recepția P00102: facturată manual din comandă înainte de rularea programată
        cls.purchase_failed = cls._purchase("P00102", 3.0)
        cls.receipt_failed = cls.purchase_failed.picking_ids
        cls._validate(cls.receipt_failed)
        cls.purchase_failed.action_create_invoice()
        env.flush_all()

    @classmethod
    def _purchase(cls, name, qty):
        purchase = cls.env["purchase.order"].create(
            {
                "name": name,
                "partner_id": cls.beta.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.desk.id,
                            "product_qty": qty,
                            "price_unit": 800.0,
                            "date_planned": fields.Datetime.now(),
                        }
                    )
                ],
            }
        )
        purchase.button_confirm()
        return purchase

    @classmethod
    def _validate(cls, picking):
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.move_ids.picked = True
        picking.button_validate()

    def _picking_url(self, picking):
        return f"id={picking.id}&model=stock.picking&view_type=form"

    def _shots(self):
        column = {"ro_RO": "Facturare automată", "en_US": "Automatic Invoicing"}
        return [
            # 1. tipul de operație Livrări: facturare automată, la validare, cu postarea facturii
            {
                "url": f"id={self.delivery_type.id}&model=stock.picking.type&view_type=form",
                "name": "01_tip_operatie_facturare_automata.png",
                "wait": ".o_form_view div[name='invoice_moment']",
                "highlight": [
                    "div[name='create_invoice_automatically']",
                    "div[name='invoice_moment']",
                    "div[name='post_invoice_automatically']",
                ],
            },
            # 2. livrarea validată, facturată la validare
            {
                "url": self._picking_url(self.delivery),
                "name": "02_livrare_facturata_la_validare.png",
                "wait": ".o_form_view div[name='move_ids'] .o_data_row",
                "click_tab": ADDITIONAL_INFO,
                "wait_after": "div[name='account_move_id']",
                "eval": "true",
                "eval_wait": 1500,
                "highlight": ["div[name='invoice_state']", "div[name='account_move_id']"],
            },
            # 3. factura clientului, postată, cu cantitatea livrată
            {
                "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                "name": "03_factura_client_postata.png",
                "wait": ".o_form_view div[name='invoice_line_ids'] .o_data_row",
                "highlight": ["div[name='invoice_line_ids'] td[name='quantity']", ".o_statusbar_status"],
            },
            # 4. factura furnizorului creată de rularea programată, în ciornă
            {
                "url": f"id={self.bill.id}&model=account.move&view_type=form",
                "name": "04_factura_furnizor_ciorna.png",
                "wait": ".o_form_view div[name='invoice_line_ids'] .o_data_row",
                "highlight": ["div[name='invoice_line_ids'] td[name='quantity']", ".o_statusbar_status"],
            },
            # 5. recepția cu facturarea eșuată: motivul și butonul de reîncercare
            {
                "url": self._picking_url(self.receipt_failed),
                "name": "05_receptie_facturare_esuata.png",
                "wait": ".o_form_view button[name='action_retry_auto_invoice']",
                "highlight": [
                    ".o_form_view .alert-danger",
                    "button[name='action_retry_auto_invoice']",
                    "div[name='invoice_state']",
                ],
            },
            # 6. Recepții, cu filtrul „Facturare automată eșuată" adăugat și coloana afișată
            {
                "url": self._picking_url(self.receipt_failed),
                "name": "06_lista_facturare_esuata.png",
                "wait": ".o_form_view",
                "eval": {
                    lang: _do_action("stock.action_picking_tree_incoming", {"search_default_auto_invoice_failed": 1})
                    + ".then(() => new Promise((r) => setTimeout(r, 1500)))"
                    + ".then(() => "
                    + SHOW_COLUMN.strip() % {"label": label}
                    + ")"
                    for lang, label in column.items()
                },
                "eval_wait": 2000,
                "highlight": [".o_searchview_facet", "td[name='invoice_state']"],
            },
        ]

    def _capture(self, lang):
        # rularea programată scrie motivul eșecului în limba ei: aici, limba capturii
        with mute_logger("odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking"):
            self.env["stock.picking"].with_context(lang=lang)._cron_generate_invoices()
        self.assertEqual(self.delivery.invoice_state, "invoiced")
        self.assertEqual(self.invoice.state, "posted")
        self.assertEqual(self.bill.state, "draft")
        self.assertEqual(self.receipt_failed.invoice_state, "failed")
        self.env.flush_all()
        self.capture_screenshots(self._shots(), lang=lang)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")
