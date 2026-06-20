# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSaleCommissionBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env["res.partner"].create({"name": "Test Partner"})

        seller_ids = [(0, 0, {"partner_id": cls.partner_a.id})]
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Test B",
                "is_storable": True,
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(cls.product_a, cls.stock_location, 1000)
        cls.env["stock.quant"]._update_available_quantity(cls.product_b, cls.stock_location, 1000)

    def _create_and_confirm_sale(self, qty_a=100, qty_b=10):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        with so.order_line.new() as line:
            line.product_id = self.product_a
            line.product_uom_qty = qty_a
        with so.order_line.new() as line:
            line.product_id = self.product_b
            line.product_uom_qty = qty_b
        so = so.save()
        so.action_confirm()
        return so

    def _validate_picking(self, picking):
        picking.action_assign()
        for move in picking.move_ids:
            if move.product_uom_qty > 0 and move.quantity == 0:
                move.quantity = move.product_uom_qty
        picking._action_done()

    def _create_invoice(self, so):
        invoice = so._create_invoices()
        invoice = Form(invoice).save()
        invoice.action_post()
        return invoice


class TestSale(TestSaleCommissionBase):
    def test_sale(self):
        so = self._create_and_confirm_sale()
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        self.assertEqual(invoice.state, "posted")

    def test_commission_compute(self):
        wizard = Form(self.env["commission.compute"])
        wizard = wizard.save()
        wizard.do_compute()

    def test_commission_update_purchase_price(self):
        so = self._create_and_confirm_sale()
        self._validate_picking(so.picking_ids)
        self._create_invoice(so)

        wizard = Form(self.env["commission.update.purchase.price"])
        wizard.for_all = True
        wizard = wizard.save()
        wizard.do_compute()

        wizard = Form(self.env["commission.update.purchase.price"])
        wizard.for_all = True
        wizard.price_from_doc = False
        wizard = wizard.save()
        wizard.do_compute()


class TestCommissionUsers(TestSaleCommissionBase):
    def test_create_commission_user(self):
        user = self.env.user
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        commission_user = self.env["commission.users"].create(
            {
                "user_id": user.id,
                "rate": 0.05,
                "manager_rate": 0.02,
                "director_rate": 0.01,
                "journal_id": journal.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(commission_user.rate, 0.05)
        self.assertEqual(commission_user.manager_rate, 0.02)
        self.assertEqual(commission_user.director_rate, 0.01)
        self.assertEqual(commission_user.name, user.name)

    def test_commission_compute_with_user(self):
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        commission_user = self.env["commission.users"].create(
            {
                "user_id": self.env.user.id,
                "rate": 0.1,
                "journal_id": journal.id,
                "company_id": self.env.company.id,
            }
        )
        so = self._create_and_confirm_sale(qty_a=10, qty_b=5)
        so.user_id = commission_user.user_id
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        invoice.invoice_user_id = commission_user.user_id

        wizard = self.env["commission.compute"].create({})
        wizard.do_compute()

        self.assertTrue(commission_user.exists())


class TestCommissionCondition(TestSaleCommissionBase):
    def test_create_commission_condition(self):
        condition = self.env["sale.commission.condition"].create(
            {
                "sequence": 10,
                "percentage": 5.0,
                "less_than_days": 30,
            }
        )
        self.assertEqual(condition.percentage, 5.0)
        self.assertEqual(condition.less_than_days, 30)
        self.assertEqual(condition.sequence, 10)

    def test_multiple_commission_conditions(self):
        cond1 = self.env["sale.commission.condition"].create(
            {"sequence": 10, "percentage": 5.0, "less_than_days": 15}
        )
        cond2 = self.env["sale.commission.condition"].create(
            {"sequence": 20, "percentage": 3.0, "less_than_days": 30}
        )
        cond3 = self.env["sale.commission.condition"].create(
            {"sequence": 30, "percentage": 1.0, "less_than_days": 60}
        )
        conditions = self.env["sale.commission.condition"].search(
            [("id", "in", [cond1.id, cond2.id, cond3.id])], order="sequence"
        )
        self.assertEqual(len(conditions), 3)
        self.assertEqual(conditions[0].percentage, 5.0)
        self.assertEqual(conditions[1].percentage, 3.0)
        self.assertEqual(conditions[2].percentage, 1.0)


class TestInvoicePurchasePrice(TestSaleCommissionBase):
    def test_purchase_price_on_invoice_line(self):
        so = self._create_and_confirm_sale(qty_a=5, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        product_lines = invoice.invoice_line_ids.filtered(
            lambda l: l.product_id == self.product_a and l.display_type == "product"
        )
        self.assertTrue(product_lines)
        for line in product_lines:
            self.assertGreater(line.purchase_price, 0, "Purchase price should be set on invoice line")

    def test_get_purchase_price_from_delivery(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        product_lines = invoice.invoice_line_ids.filtered(
            lambda l: l.product_id == self.product_a and l.display_type == "product"
        )
        self.assertTrue(product_lines)
        line = product_lines[0]
        purchase_price = line.get_purchase_price()
        self.assertGreater(purchase_price, 0)

    def test_compute_purchase_price_on_invoice(self):
        so = self._create_and_confirm_sale(qty_a=5, qty_b=5)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        invoice.compute_purchase_price()

        for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product"):
            self.assertGreater(line.purchase_price, 0)

    def test_sale_user_id_on_invoice_line(self):
        so = self._create_and_confirm_sale(qty_a=5, qty_b=0)
        so.user_id = self.env.user
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        product_lines = invoice.invoice_line_ids.filtered(
            lambda l: l.product_id == self.product_a and l.display_type == "product"
        )
        self.assertTrue(product_lines)
        for line in product_lines:
            self.assertEqual(line.sale_user_id, self.env.user)


class TestSaleMarginReport(TestSaleCommissionBase):
    def test_margin_report_after_invoice(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=5)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertTrue(report_lines, "Margin report should have entries after posting invoice")

    def test_margin_report_profit_fields(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        report_lines = self.env["sale.margin.report"].search(
            [("invoice_id", "=", invoice.id), ("product_id", "=", self.product_a.id)]
        )
        self.assertTrue(report_lines)
        for line in report_lines:
            self.assertGreater(line.sale_val, 0, "Sale value should be positive")
            self.assertGreater(line.stock_val, 0, "Stock value should be positive after delivery")

    def test_commission_paid_flag(self):
        so = self._create_and_confirm_sale(qty_a=5, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertTrue(report_lines)
        report_lines.action_set_commission_paid()
        for line in report_lines:
            self.assertTrue(line.commission_paid)

    def test_cron_update_purchase_price(self):
        so = self._create_and_confirm_sale(qty_a=5, qty_b=5)
        self._validate_picking(so.picking_ids)
        self._create_invoice(so)
        self.env["sale.margin.report"].cron_update_purchase_price()


class TestCommissionComputeWithDaysLimit(TestSaleCommissionBase):
    def test_commission_compute_no_days_limit(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        self.env["ir.config_parameter"].sudo().set_param("deltatech_sale_commission.days_for_commission", "")

        wizard = self.env["commission.compute"].create({})
        wizard.do_compute()

        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertTrue(report_lines.exists())

    def test_commission_compute_with_days_limit(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        self.env["ir.config_parameter"].sudo().set_param("deltatech_sale_commission.days_for_commission", "30")

        wizard = self.env["commission.compute"].create({})
        wizard.do_compute()

        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertTrue(report_lines.exists())
