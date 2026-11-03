# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Facturare din transferuri și loturi", în RO (fișa) și EN
# (readme/USAGE.md), pe planul de conturi românesc (`setup_country("ro")`).
#
# Seed: comanda S00101 (10 scaune + 2 birouri) livrată parțial (6 scaune + 2 birouri, restul în
# livrare ulterioară), comanda S00102 (10 scaune) livrată integral și facturată doar 5, recepția
# comenzii P00101 (5 birouri) cu numărul facturii furnizorului și lotul BATCH/00101 cu livrarea
# comenzii S00103. Facturile se emit între fazele de capturi; la final, un retur de 2 scaune din
# livrarea facturată a comenzii S00101 și nota de credit emisă din retur.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,deltatech_invoice_picking,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

ADDITIONAL_INFO = {"ro_RO": "Informații suplimentare", "en_US": "Additional Info"}


def _do_action(action):
    """JS: deschide o acțiune în locul ecranului curent."""
    options = json.dumps({"clearBreadcrumbs": True})
    return f"odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(action)}, {options})"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestInvoicePickingScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_invoice_picking"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        cls.prepare_ro_company()
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
        for picking_type, names in (
            (warehouse.out_type_id, {"ro_RO": "Livrări", "en_US": "Delivery Orders"}),
            (warehouse.in_type_id, {"ro_RO": "Recepții", "en_US": "Receipts"}),
        ):
            # fără loturi automate: în capturi apare doar lotul seedat
            picking_type.auto_batch = False
            for lang, name in names.items():
                picking_type.with_context(lang=lang).name = name
        for product in cls.chair | cls.desk:
            env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, 100.0)

        ro = env.ref("base.ro").id
        cls.alfa, cls.gamma, cls.delta, cls.beta = env["res.partner"].create(
            [
                {"name": "Alfa Construct SRL", "country_id": ro, "lang": "ro_RO"},
                {"name": "Gamma Retail SRL", "country_id": ro, "lang": "ro_RO"},
                {"name": "Delta Office SRL", "country_id": ro, "lang": "ro_RO"},
                {"name": "Beta Mobila SRL", "country_id": ro, "lang": "ro_RO"},
            ]
        )

        # numerele fixe: secvențele comenzilor și loturilor nu se anulează la rollback
        cls.order = cls._sale_order("S00101", cls.alfa, [(cls.chair, 10.0), (cls.desk, 2.0)])
        cls.picking = cls.order.picking_ids
        # lista de prețuri a companiei de test are nume englezesc tehnic
        pricelist = cls.order.pricelist_id
        pricelist.with_context(lang="en_US").name = "Standard pricelist"
        pricelist.with_context(lang="ro_RO").name = "Listă de prețuri standard"
        # livrare parțială: 6 scaune din 10 și ambele birouri; restul rămâne în livrarea ulterioară
        cls._validate(cls.picking, {cls.chair: 6.0, cls.desk: 2.0})

        cls.order_partial = cls._sale_order("S00102", cls.gamma, [(cls.chair, 10.0)])
        cls.picking_partial = cls.order_partial.picking_ids
        cls._validate(cls.picking_partial, {cls.chair: 10.0})

        purchase = env["purchase.order"].create(
            {
                "name": "P00101",
                "partner_id": cls.beta.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.desk.id,
                            "product_qty": 5.0,
                            "price_unit": 800.0,
                            "date_planned": fields.Datetime.now(),
                        }
                    )
                ],
            }
        )
        purchase.button_confirm()
        cls.receipt = purchase.picking_ids
        cls._validate(cls.receipt, {cls.desk: 5.0})
        cls.receipt.supplier_invoice_number = "BM-2026-0457"

        order_batch = cls._sale_order("S00103", cls.delta, [(cls.chair, 3.0)])
        # lotul se formează înainte de validare: _sanity_check refuză transferurile efectuate
        cls.batch = env["stock.picking.batch"].create({"picking_ids": [Command.set(order_batch.picking_ids.ids)]})
        cls.batch.name = "BATCH/00101"
        cls._validate(order_batch.picking_ids, {cls.chair: 3.0})
        env.flush_all()

    @classmethod
    def _sale_order(cls, name, partner, lines):
        order = cls.env["sale.order"].create(
            {
                "name": name,
                "partner_id": partner.id,
                "user_id": cls.env.ref("base.user_admin").id,
                "order_line": [Command.create({"product_id": p.id, "product_uom_qty": qty}) for p, qty in lines],
            }
        )
        order.action_confirm()
        return order

    @classmethod
    def _validate(cls, picking, quantities):
        for move in picking.move_ids:
            move.quantity = quantities[move.product_id]
        picking.move_ids.picked = True
        picking.with_context(skip_backorder=True).button_validate()

    def _invoice_from_picking(self):
        """Factura emisă de butonul Invoice al livrării, cu asistentul standard (Regular invoice)."""
        action = self.picking.action_create_invoice()
        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(**action["context"])
            .create({"advance_payment_method": "delivered"})
        )
        wizard.create_invoices()
        invoice = self.picking.account_move_id
        invoice.invoice_date = fields.Date.context_today(invoice)
        invoice.action_post()
        return invoice

    def _partial_invoice(self):
        """Factură manuală pe comanda S00102, doar pentru 5 din cele 10 scaune livrate."""
        sale_line = self.order_partial.order_line
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.gamma.id,
                "invoice_date": fields.Date.context_today(self.order_partial),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.chair.id,
                            "quantity": 5.0,
                            "price_unit": 450.0,
                            "tax_ids": [Command.set(sale_line.tax_ids.ids)],
                            "sale_line_ids": [Command.set(sale_line.ids)],
                        }
                    )
                ],
            }
        )
        invoice.update_pickings()
        invoice.action_post()
        return invoice

    def _picking_url(self, picking):
        return f"id={picking.id}&model=stock.picking&view_type=form"

    def _shots_before(self):
        deliveries = {
            "type": "ir.actions.act_window",
            "name": None,
            "res_model": "stock.picking",
            "views": [[False, "list"], [False, "form"]],
            "domain": [["picking_type_code", "=", "outgoing"]],
            "context": {"search_default_to_invoice": 1, "restricted_picking_type_code": "outgoing"},
        }
        return [
            {
                "url": self._picking_url(self.picking),
                "name": "01_livrari_de_facturat.png",
                "wait": ".o_form_view",
                "eval": {
                    lang: _do_action(dict(deliveries, name=name))
                    for lang, name in (("ro_RO", "Livrări"), ("en_US", "Deliveries"))
                },
                "eval_wait": 2500,
                "highlight": [".o_searchview_facet", ".o_data_row td[name='name']"],
            },
            {
                "url": self._picking_url(self.picking),
                "name": "02_livrare_buton_factura.png",
                "wait": ".o_form_view button[name='action_create_invoice']",
                "highlight": ["button[name='action_create_invoice']", "div[name='move_ids'] td[name='quantity']"],
            },
            {
                "url": self._picking_url(self.picking),
                "name": "03_asistent_facturare.png",
                "wait": ".o_form_view button[name='action_create_invoice']",
                "click_btn": "button[name='action_create_invoice']",
                "wait_after": ".modal .o_form_view",
                "settle": 2000,
                "highlight": [".modal div[name='advance_payment_method']", ".modal button[name='create_invoices']"],
            },
            {
                "url": self._picking_url(self.receipt),
                "name": "07_receptie_numar_factura.png",
                "wait": ".o_form_view button[name='action_create_supplier_invoice']",
                "highlight": ["div[name='supplier_invoice_number']", "button[name='action_create_supplier_invoice']"],
            },
            {
                "url": f"id={self.batch.id}&model=stock.picking.batch&view_type=form",
                "name": "09_lot_buton_factura.png",
                "wait": ".o_form_view button[name='action_create_invoice']",
                "highlight": ["button[name='action_create_invoice']"],
            },
            {
                "url": f"id={self.order.id}&model=sale.order&view_type=form",
                "name": "10_comanda_facturare_fortata.png",
                "wait": ".o_form_view",
                "click_tab": "Other Info",
                "wait_after": "div[name='force_invoice_order']",
                "highlight": ["div[name='force_invoice_order']"],
            },
        ]

    def _shots_after(self, invoice, bill):
        return [
            {
                "url": f"id={invoice.id}&model=account.move&view_type=form",
                "name": "04_factura_din_livrare.png",
                "wait": ".o_form_view div[name='invoice_line_ids'] .o_data_row",
                "highlight": ["div[name='invoice_line_ids'] td[name='quantity']", "div[name='amount_total']"],
            },
            {
                "url": self._picking_url(self.picking),
                "name": "05_livrare_facturata.png",
                "wait": ".o_form_view div[name='move_ids'] .o_data_row",
                "click_tab": ADDITIONAL_INFO,
                "wait_after": "div[name='account_move_id']",
                "highlight": ["div[name='account_move_id']", "div[name='to_invoice']"],
            },
            {
                "url": self._picking_url(self.picking_partial),
                "name": "06_livrare_facturata_partial.png",
                "wait": ".o_form_view div[name='move_ids'] .o_data_row",
                "click_tab": ADDITIONAL_INFO,
                "wait_after": "div[name='account_move_id']",
                # fila se mai randează o dată după click; evidențierea se pune după ea
                "eval": "true",
                "eval_wait": 1500,
                "highlight": [
                    "div[name='account_move_id']",
                    "div[name='to_invoice']",
                    "button[name='action_create_invoice']",
                ],
            },
            {
                "url": f"id={bill.id}&model=account.move&view_type=form",
                "name": "08_factura_furnizor.png",
                "wait": ".o_form_view div[name='invoice_line_ids'] .o_data_row",
                "highlight": [
                    "button[name='action_view_source_purchase_orders']",
                    "div[name='invoice_line_ids'] td[name='quantity']",
                ],
            },
        ]

    def _return_after_invoice(self):
        """Retur de 2 scaune din livrarea facturată a comenzii S00101."""
        return_picking = self.picking._create_return()
        return_picking.move_ids.filtered(lambda m: m.product_id != self.chair).unlink()
        return_picking.move_ids.quantity = 2.0
        return_picking.move_ids.picked = True
        return_picking.button_validate()
        return return_picking

    def _refund_from_return(self, return_picking):
        """Nota de credit emisă de butonul Facturează al returului, cu asistentul standard."""
        action = return_picking.action_create_invoice()
        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(**action["context"])
            .create({"advance_payment_method": "delivered"})
        )
        wizard.create_invoices()
        refund = return_picking.account_move_id
        refund.invoice_date = fields.Date.context_today(refund)
        refund.action_post()
        return refund

    def _shots_return(self, return_picking):
        return [
            {
                "url": self._picking_url(return_picking),
                "name": "11_retur_de_facturat.png",
                "wait": ".o_form_view div[name='move_ids'] .o_data_row",
                "click_tab": ADDITIONAL_INFO,
                "wait_after": "div[name='to_invoice']",
                "eval": "true",
                "eval_wait": 1500,
                "highlight": ["button[name='action_create_invoice']", "div[name='to_invoice']"],
            },
        ]

    def _shots_refund(self, refund):
        return [
            {
                "url": f"id={refund.id}&model=account.move&view_type=form",
                "name": "12_nota_credit_retur.png",
                "wait": ".o_form_view div[name='invoice_line_ids'] .o_data_row",
                "highlight": ["div[name='invoice_line_ids'] td[name='quantity']", "div[name='amount_total']"],
            },
        ]

    def _capture(self, lang):
        self.capture_screenshots(self._shots_before(), lang=lang)
        invoice = self._invoice_from_picking()
        self._partial_invoice()
        action = self.receipt.action_create_supplier_invoice()
        bill = self.env["account.move"].browse(action["res_id"])
        self.env.flush_all()
        self.capture_screenshots(self._shots_after(invoice, bill), lang=lang)
        return_picking = self._return_after_invoice()
        self.assertTrue(return_picking.to_invoice)
        self.assertFalse(return_picking.account_move_id)
        self.env.flush_all()
        self.capture_screenshots(self._shots_return(return_picking), lang=lang)
        refund = self._refund_from_return(return_picking)
        self.assertEqual(refund.move_type, "out_refund")
        self.assertFalse(return_picking.to_invoice)
        self.env.flush_all()
        self.capture_screenshots(self._shots_refund(refund), lang=lang)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")
