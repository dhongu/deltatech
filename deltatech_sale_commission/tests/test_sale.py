# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form, new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleCommissionBase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # The accounting test user lacks sales/stock rights; grant them so we
        # can create sale orders, commission records and validate the delivery.
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        cls.env.user.group_ids |= cls.env.ref("stock.group_stock_manager")
        cls.env.user.group_ids |= cls.env.ref("deltatech_sale_commission.group_commission_manager")

        # Customer for the sale orders. The Romanian localization installed on
        # the test database requires a full address (country, state, city,
        # street) to post invoices.
        ro_country = cls.env.ref("base.ro")
        ro_state = cls.env["res.country.state"].search([("country_id", "=", ro_country.id)], limit=1)
        cls.partner_a = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "country_id": ro_country.id,
                "state_id": ro_state.id,
                "city": "București",
                "street": "Str. Test nr. 1",
            }
        )
        # Separate vendor used as the products' supplier (seller).
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})

        seller_ids = [(0, 0, {"partner_id": cls.vendor.id})]
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
        # Seed stock in the warehouse used by the test company so the delivery
        # has stock to move out.
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
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
        cond1 = self.env["sale.commission.condition"].create({"sequence": 10, "percentage": 5.0, "less_than_days": 15})
        cond2 = self.env["sale.commission.condition"].create({"sequence": 20, "percentage": 3.0, "less_than_days": 30})
        cond3 = self.env["sale.commission.condition"].create({"sequence": 30, "percentage": 1.0, "less_than_days": 60})
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
        # sale.margin.report is a SQL view; action_set_commission_paid writes to
        # the underlying account.move.line. Flush so the write reaches the DB,
        # then re-read the view to observe the flag.
        self.env.flush_all()
        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
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

        self.env["ir.config_parameter"].sudo().set_str("deltatech_sale_commission.days_for_commission", "")

        wizard = self.env["commission.compute"].create({})
        wizard.do_compute()

        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertTrue(report_lines.exists())

    def test_commission_compute_with_days_limit(self):
        so = self._create_and_confirm_sale(qty_a=10, qty_b=0)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)

        self.env["ir.config_parameter"].sudo().set_int("deltatech_sale_commission.days_for_commission", 30)

        wizard = self.env["commission.compute"].create({})
        wizard.do_compute()

        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertTrue(report_lines.exists())


class TestCommissionValues(TestSaleCommissionBase):
    """Explicit values of the margin/commission report.

    product A: cost 100, price 150; product B: cost 70, price 150 (see base).
    Standard costing: the delivery is valued at the product cost, so the
    purchase price on the invoice line comes from the delivery move.
    In 20 ``stock.move.value`` is negative on outgoing moves; the values below
    are the ones computed on 19.0 and must stay identical.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_journal = cls.company_data["default_journal_sale"]
        cls.commission_user = cls.env["commission.users"].create(
            {
                "user_id": cls.env.user.id,
                "rate": 0.1,
                "manager_rate": 0.02,
                "director_rate": 0.01,
                "journal_id": cls.sale_journal.id,
                "company_id": cls.env.company.id,
            }
        )

    def _invoice(self, qty_a=10, qty_b=4):
        so = self._create_and_confirm_sale(qty_a=qty_a, qty_b=qty_b)
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        self.assertEqual(invoice.journal_id, self.sale_journal)
        return so, invoice

    def _report_line(self, invoice, product):
        # sale.margin.report is a SQL view over account.move.line: flush the
        # writes and drop the cache to read the view again
        self.env.flush_all()
        self.env.invalidate_all()
        line = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id), ("product_id", "=", product.id)])
        self.assertEqual(len(line), 1)
        return line

    def test_purchase_price_from_delivery(self):
        _so, invoice = self._invoice()
        line_a = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        line_b = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_b)
        # the delivery move value is negative in 20, the cost price must stay positive
        self.assertAlmostEqual(line_a.get_purchase_price(), 100.0)
        self.assertAlmostEqual(line_b.get_purchase_price(), 70.0)
        self.assertAlmostEqual(line_a.purchase_price, 100.0)
        self.assertAlmostEqual(line_b.purchase_price, 70.0)

    def test_report_values(self):
        _so, invoice = self._invoice()
        line_a = self._report_line(invoice, self.product_a)
        self.assertRecordValues(
            line_a,
            [
                {
                    "user_id": self.env.user.id,
                    "product_uom_qty": 10.0,
                    "purchase_price": 100.0,
                    "sale_val": 1500.0,
                    "stock_val": 1000.0,
                    "profit_val": 500.0,
                    "markup": 50.0,
                    "commission_computed": 50.0,
                    "commission_manager_computed": 10.0,
                    "commission_director_computed": 5.0,
                    "commission": 0.0,
                    "commission_paid": False,
                }
            ],
        )
        self.assertAlmostEqual(line_a.profit_margin, 100 * 500 / 1500, places=2)

        line_b = self._report_line(invoice, self.product_b)
        self.assertRecordValues(
            line_b,
            [
                {
                    "product_uom_qty": 4.0,
                    "purchase_price": 70.0,
                    "sale_val": 600.0,
                    "stock_val": 280.0,
                    "profit_val": 320.0,
                    "commission_computed": 32.0,
                    "commission_manager_computed": 6.4,
                    "commission_director_computed": 3.2,
                }
            ],
        )

    def test_report_read_group_markup(self):
        """markup / profit_margin are computed on the aggregated values, not averaged."""
        _so, invoice = self._invoice()
        self.env.flush_all()
        groups = self.env["sale.margin.report"]._read_group(
            [("invoice_id", "=", invoice.id)],
            [],
            ["sale_val:sum", "stock_val:sum", "profit_val:sum", "markup:avg", "profit_margin:avg"],
        )
        sale_val, stock_val, profit_val, markup, profit_margin = groups[0]
        self.assertAlmostEqual(sale_val, 2100.0)
        self.assertAlmostEqual(stock_val, 1280.0)
        self.assertAlmostEqual(profit_val, 820.0)
        self.assertAlmostEqual(markup, 100 * 820 / 1280, places=4)
        self.assertAlmostEqual(profit_margin, 100 * 820 / 2100, places=4)

        result = self.env["sale.margin.report"].formatted_read_group(
            [("invoice_id", "=", invoice.id)], ["user_id"], ["markup:avg", "profit_margin:avg"]
        )
        self.assertAlmostEqual(result[0]["markup:avg"], 100 * 820 / 1280, places=4)
        self.assertAlmostEqual(result[0]["profit_margin:avg"], 100 * 820 / 2100, places=4)

    def test_commission_compute_values(self):
        self.env["ir.config_parameter"].sudo().set_str("deltatech_sale_commission.days_for_commission", "")
        _so, invoice = self._invoice()
        self.env.flush_all()
        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        wizard = self.env["commission.compute"].with_context(active_ids=report_lines.ids).create({})
        self.assertEqual(wizard.invoice_line_ids, report_lines)
        wizard.do_compute()

        line_a = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        line_b = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_b)
        self.assertAlmostEqual(line_a.commission, 50.0)
        self.assertAlmostEqual(line_b.commission, 32.0)
        self.assertAlmostEqual(self._report_line(invoice, self.product_a).commission, 50.0)

        # set paid from the report writes on the invoice line
        report_lines.action_set_commission_paid()
        self.assertTrue(line_a.commission_paid)
        self.assertTrue(line_b.commission_paid)

    def test_commission_days_limit_unpaid_invoice(self):
        """With a days limit, an unpaid invoice gets no commission."""
        self.env["ir.config_parameter"].sudo().set_int("deltatech_sale_commission.days_for_commission", 30)
        _so, invoice = self._invoice()
        self.env.flush_all()
        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.env["commission.compute"].with_context(active_ids=report_lines.ids).create({}).do_compute()
        for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product"):
            self.assertEqual(line.commission, 0.0)

    def test_commission_days_limit_paid_invoice(self):
        """With a days limit, an invoice paid in time gets the full commission."""
        self.env["ir.config_parameter"].sudo().set_int("deltatech_sale_commission.days_for_commission", 30)
        _so, invoice = self._invoice()
        self.env["account.payment.register"].with_context(active_model="account.move", active_ids=invoice.ids).create(
            {}
        )._create_payments()
        self.assertEqual(invoice.payment_state, "paid")
        self.env.flush_all()
        report_lines = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.env["commission.compute"].with_context(active_ids=report_lines.ids).create({}).do_compute()
        line_a = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertAlmostEqual(line_a.commission, 50.0)

    def test_refund_values(self):
        _so, invoice = self._invoice(qty_a=10, qty_b=4)
        refund = invoice._reverse_moves()
        refund.action_post()
        line_a = self._report_line(refund, self.product_a)
        self.assertRecordValues(
            line_a,
            [
                {
                    "move_type": "out_refund",
                    "product_uom_qty": -10.0,
                    "sale_val": -1500.0,
                    "stock_val": -1000.0,
                    "profit_val": -500.0,
                    "commission_computed": -50.0,
                }
            ],
        )
        self.env["commission.compute"].with_context(active_ids=line_a.ids).create({}).do_compute()
        refund_line = refund.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertAlmostEqual(refund_line.commission, -50.0)

    def test_sale_user_detail_sale_order(self):
        """Salesperson taken from the sale order instead of the invoice."""
        salesman = new_test_user(self.env, login="commission_salesman", groups="sales_team.group_sale_salesman")
        self.commission_user.user_id = salesman
        self.env["ir.config_parameter"].sudo().set_str("sale_commission.sale_user_detail", "sale")
        self.env["sale.margin.report"].init()

        so = self._create_and_confirm_sale(qty_a=10, qty_b=4)
        so.user_id = salesman
        self._validate_picking(so.picking_ids)
        invoice = self._create_invoice(so)
        invoice.invoice_user_id = self.env.user
        line_a = self._report_line(invoice, self.product_a)
        self.assertEqual(line_a.user_id, salesman)
        self.assertAlmostEqual(line_a.commission_computed, 50.0)

        # back to the invoice salesperson: no commission row for the invoice user
        self.env["ir.config_parameter"].sudo().set_str("sale_commission.sale_user_detail", "invoice")
        self.env["sale.margin.report"].init()
        self.env.invalidate_all()
        line_a = self._report_line(invoice, self.product_a)
        self.assertEqual(line_a.user_id, self.env.user)
        self.assertAlmostEqual(line_a.commission_computed, 0.0)
