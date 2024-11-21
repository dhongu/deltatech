# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "product",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.stock_location = self.env.ref("stock.stock_location_stock")

        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": self.product_a.id,
                "inventory_quantity": 10000,
                "location_id": self.stock_location.id,
            }
        ).action_apply_inventory()

        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": self.product_b.id,
                "inventory_quantity": 10000,
                "location_id": self.stock_location.id,
            }
        ).action_apply_inventory()

        currency_eur = self.env.ref("base.EUR")
        currency_eur.write({"active": True})
        self.journal_eur = self.env["account.journal"].create(
            {
                "name": "Test Journal EUR",
                "type": "sale",
                "code": "SJ1",
                "currency_id": currency_eur.id,
            }
        )
        currency_usd = self.env.ref("base.USD")
        currency_usd.write({"active": True})
        self.journal_usd = self.env["account.journal"].create(
            {
                "name": "Test Journal USD",
                "type": "sale",
                "code": "SJ2",
                "currency_id": currency_usd.id,
            }
        )
        self.team_eur = self.env["crm.team"].create(
            {
                "name": "Test Team EUR",
                "journal_id": self.journal_eur.id,
            }
        )
        self.team_usd = self.env["crm.team"].create(
            {
                "name": "Test Team USD",
                "journal_id": self.journal_usd.id,
            }
        )

    def test_sale_wizard_invoice(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so.action_confirm()

        wizard = Form(self.env["sale.advance.payment.inv"].with_context(active_ids=self.so.ids))
        wizard.advance_payment_method = "percentage"
        wizard.amount = "50"
        wizard = wizard.save()
        wizard.create_invoices()

    def test_sale(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so.action_confirm()

        pick = self.so.picking_ids
        pick.move_lines.write({"quantity_done": 1})
        pick.button_validate()

        self.so.with_context(default_journal_id=self.so.team_id.journal_id.id)._create_invoices()

        self.so.invoice_ids.action_post()
        # self.so.invoice_ids.action_switch_invoice_into_refund_credit_note()

    def test_sale_eur_percentage(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        so.team_id = self.team_eur
        # so.price_list_id.write({'currency_id': self.ref('base.EUR').id})
        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so.action_confirm()

        wizard = Form(self.env["sale.advance.payment.inv"].with_context(active_ids=self.so.ids))
        wizard.advance_payment_method = "percentage"
        wizard.amount = "50"
        wizard = wizard.save()
        wizard.journal_id.write({"currency_id": self.env.ref("base.EUR").id})
        wizard.create_invoices()

    def test_sale_eur_fix(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        so.team_id = self.team_usd
        # so.price_list_id.write({'currency_id': self.ref('base.EUR').id})
        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so.action_confirm()

        wizard = Form(self.env["sale.advance.payment.inv"].with_context(active_ids=self.so.ids))
        wizard.advance_payment_method = "fixed"
        wizard.fixed_amount = "50"
        wizard = wizard.save()
        wizard.journal_id.write({"currency_id": self.env.ref("base.USD").id})
        wizard.create_invoices()

        self.so.invoice_ids.action_post()
