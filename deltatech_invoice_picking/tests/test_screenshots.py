# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Facturare din transferuri" — generate în timpul
# testelor, în limba RO (fișa) și EN (readme/USAGE.md), pe compania
# „Demo Distribuție SRL" în RON.
#
# Seedează comenzi de vânzare de 10 buc. livrate parțial (6 buc.): una încă
# nefacturată, una facturată din livrare și una a cărei livrare e în listă;
# o recepție cu numărul facturii furnizorului, una facturată și un lot de livrări
# validat.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_invoice_picking,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestInvoicePickingScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_invoice_picking"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Distribuție SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in (
            "stock.group_stock_manager",
            "sales_team.group_sale_manager",
            "purchase.group_purchase_manager",
        ):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]

        cls.warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.warehouse.write({"name": "Depozit central", "code": "DC"})
        # agentul de vânzări al facturilor: utilizatorul de test are un nume de glumă
        env.user.name = "Ana Popescu"
        # tipurile de operație sunt create înaintea limbii RO: numele RO se pun ca traducere
        cls.warehouse.out_type_id.update_field_translations("name", {"ro_RO": "Livrări", "en_US": "Delivery Orders"})
        cls.warehouse.in_type_id.update_field_translations("name", {"ro_RO": "Recepții", "en_US": "Receipts"})
        # fără loturi automate: fiecare livrare ar primi altfel un lot propriu în capturi
        (cls.warehouse.out_type_id | cls.warehouse.in_type_id).auto_batch = False

        Partner = env["res.partner"]
        ro = env.ref("base.ro").id
        cls.alfa = Partner.create({"name": "Alfa Construct SRL", "country_id": ro, "city": "Cluj-Napoca"})
        cls.beta = Partner.create({"name": "Beta Instal SRL", "country_id": ro, "city": "Iași"})
        cls.vendor = Partner.create({"name": "Gama Materiale SRL", "country_id": ro, "city": "Brașov"})

        cls.product = env["product.product"].create(
            {
                "name": "Robinet sferic 1/2",
                "is_storable": True,
                "invoice_policy": "delivery",
                "purchase_method": "receive",
                "list_price": 45.0,
                "standard_price": 30.0,
                "taxes_id": [Command.set(cls.company_data["default_tax_sale"].ids)],
                "supplier_taxes_id": [Command.set(cls.company_data["default_tax_purchase"].ids)],
            }
        )
        env["stock.quant"]._update_available_quantity(cls.product, cls.warehouse.lot_stock_id, 100.0)

        # 1–2. livrare de 6 buc. din 10, validată, încă nefacturată
        cls.picking_open = cls._deliver(cls._sale_order(cls.alfa), 6.0)
        # 3–4: aceeași livrare se facturează în test, între capturi (vezi _capture)
        # 5. o a doua livrare nefacturată, la alt client, în lista „De facturat"
        cls._deliver(cls._sale_order(cls.beta, qty=4.0), 4.0)

        # 6. recepție validată, cu numărul facturii furnizorului completat
        cls.receipt_open = cls._receive(cls._purchase_order(), "FF-2026-0145")
        # 7: aceeași recepție se facturează în test, între capturi (vezi _capture)

        # 8. lot de două livrări validate
        # un lot primește doar transferuri nevalidate: se formează întâi, apoi se validează
        delta = Partner.create({"name": "Delta Tehnic SRL", "country_id": ro, "city": "Timișoara"})
        epsilon = Partner.create({"name": "Epsilon Grup SRL", "country_id": ro, "city": "Constanța"})
        batch_orders = cls._sale_order(delta, qty=3.0) | cls._sale_order(epsilon, qty=2.0)
        batch_pickings = env["stock.picking"].search(
            [("origin", "in", batch_orders.mapped("name")), ("state", "not in", ("done", "cancel"))]
        )
        cls.batch = env["stock.picking.batch"].create(
            {
                "picking_type_id": cls.warehouse.out_type_id.id,
                "picking_ids": [Command.set(batch_pickings.ids)],
                "company_id": company.id,
            }
        )
        cls.batch.action_confirm()
        for move in batch_pickings.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        cls.batch.action_done()
        # Livrări cu filtrul „De facturat" aplicat la deschidere
        cls.deliveries_action = env["ir.actions.act_window"].create(
            {
                "name": "Deliveries",
                "res_model": "stock.picking",
                "view_mode": "list,form",
                "domain": [("picking_type_code", "=", "outgoing")],
                "context": "{'search_default_to_invoice': 1}",
                "search_view_id": env.ref("stock.view_picking_internal_search").id,
            }
        )
        cls.deliveries_action.update_field_translations("name", {"ro_RO": "Livrări", "en_US": "Deliveries"})
        env.flush_all()

    @classmethod
    def _sale_order(cls, partner, qty=10.0):
        order = cls.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [Command.create({"product_id": cls.product.id, "product_uom_qty": qty})],
            }
        )
        order.action_confirm()
        return order

    @classmethod
    def _deliver(cls, order, qty):
        """Validează prima livrare a comenzii cu ``qty`` buc.; restul rămâne în backorder."""
        picking = order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))[:1]
        picking.move_ids.quantity = qty
        picking.move_ids.picked = True
        res = picking.button_validate()
        if isinstance(res, dict) and res.get("res_model") == "stock.backorder.confirmation":
            wizard = Form(cls.env[res["res_model"]].with_context(**res["context"])).save()
            wizard.process()
        return picking

    @classmethod
    def _invoice_pickings(cls, pickings):
        """Factura din transfer, ca butonul „Facturează" urmat de „Creează ciornă"."""
        action = pickings.action_create_invoice()
        context = action["context"]
        wizard = cls.env["sale.advance.payment.inv"].with_context(**context).create({})
        wizard.create_invoices()
        return pickings.account_move_id

    @classmethod
    def _purchase_order(cls):
        order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "order_line": [Command.create({"product_id": cls.product.id, "product_qty": 20.0, "price_unit": 30.0})],
            }
        )
        order.button_confirm()
        return order

    @classmethod
    def _receive(cls, order, supplier_invoice_number):
        picking = order.picking_ids[:1]
        picking.move_ids.quantity = 20.0
        picking.move_ids.picked = True
        picking.button_validate()
        picking.supplier_invoice_number = supplier_invoice_number
        return picking

    def _shots(self, invoice=None, bill=None):
        picking_form = "model=stock.picking&view_type=form"
        tab_extra = {"ro_RO": "Informații suplimentare", "en_US": "Additional Info"}
        return [
            # 1. livrarea validată, cu butonul Facturează și bifa De facturat
            {
                "url": f"id={self.picking_open.id}&{picking_form}",
                "name": "01_livrare_de_facturat.png",
                "wait": ".o_form_view",
                "click_tab": tab_extra,
                "settle": 2500,
                "highlight": ["button[name='action_create_invoice']", "div[name='to_invoice']"],
            },
            # 2. fereastra standard de creare a facturii, deschisă din livrare
            {
                "url": f"id={self.picking_open.id}&{picking_form}",
                "name": "02_fereastra_creare_factura.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='action_create_invoice']",
                "wait_after": ".modal .o_form_view",
                "settle": 2500,
                "highlight": [".modal button[name='create_invoices']"],
            },
            # 3. factura creată din livrare: linia de 6 buc. din comanda de 10 buc.
            {
                "url": f"id={invoice.id if invoice else 0}&model=account.move&view_type=form",
                "name": "03_factura_din_livrare.png",
                "wait": ".o_form_view",
                "click_tab": "Invoice Lines",
                "settle": 2500,
                "highlight": ["div[name='invoice_line_ids'] td[name='quantity']"],
                "full": True,
            },
            # 4. livrarea după facturare
            {
                "url": f"id={self.picking_open.id}&{picking_form}",
                "name": "04_livrare_facturata.png",
                "wait": ".o_form_view",
                "click_tab": tab_extra,
                "settle": 2500,
                "highlight": ["div[name='account_move_id']", "div[name='to_invoice']"],
            },
            # 5. lista livrărilor filtrată De facturat, cu o livrare selectată și meniul Acțiuni
            {
                "url": f"action={self.deliveries_action.id}&view_type=list",
                "name": "05_livrari_de_facturat.png",
                "wait": ".o_list_view .o_data_row",
                "eval": (
                    "(async () => {"
                    "const row = [...document.querySelectorAll('.o_data_row')]"
                    ".find(r => /Efectuat|Done/.test(r.textContent));"
                    "row?.querySelector('.o_list_record_selector input')?.click();"
                    "await new Promise(r => setTimeout(r, 1000));"
                    "const btn = [...document.querySelectorAll('.o_control_panel button')]"
                    ".find(b => ['Acțiuni', 'Actions'].includes(b.textContent.trim()));"
                    "btn?.click();"
                    "})()"
                ),
                "settle": 3000,
            },
            # 6. recepția cu numărul facturii furnizorului și butonul Factură
            {
                "url": f"id={self.receipt_open.id}&{picking_form}",
                "name": "06_receptie_nr_factura.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "highlight": ["div[name='supplier_invoice_number']", "button[name='action_create_supplier_invoice']"],
            },
            # 7. factura furnizorului creată din recepție
            {
                "url": f"id={bill.id if bill else 0}&model=account.move&view_type=form",
                "name": "07_factura_furnizor.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "highlight": ["div[name='ref']"],
                "full": True,
            },
            # 8. lotul de livrări validat, cu butonul Facturează
            {
                "url": f"id={self.batch.id}&model=stock.picking.batch&view_type=form",
                "name": "08_lot_facturare.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "highlight": ["button[name='action_create_invoice']"],
            },
        ]

    def _capture(self, **kwargs):
        """Capturile urmăresc aceleași documente: livrarea și recepția se facturează între capturi."""
        self.capture_screenshots(self._shots()[:2], **kwargs)
        invoice = self._invoice_pickings(self.picking_open)
        self.capture_screenshots(self._shots(invoice)[2:6], **kwargs)
        self.receipt_open.action_create_supplier_invoice()
        bill = self.receipt_open.account_move_id
        self.capture_screenshots(self._shots(invoice, bill)[6:], **kwargs)

    def test_capture_fise(self):
        self._capture(hide_systray=True)

    def test_capture_usage(self):
        self._capture(lang="en_US", hide_systray=True)
