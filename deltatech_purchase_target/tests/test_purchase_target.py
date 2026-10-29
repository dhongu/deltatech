# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPurchaseTarget(AccountTestInvoicingCommon):
    """Achieved vs target: only the bills of the manufacturer count, credit notes are deducted,
    the quarters are cumulated and a product in two categories counts in each of them."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("purchase.group_purchase_manager")
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        Partner = cls.env["res.partner"]
        cls.manufacturer = Partner.create({"name": "Manufacturer TGT", "is_manufacturer": True})
        cls.reseller = Partner.create({"name": "Reseller TGT"})
        Category = cls.env["product.public.category"]
        cls.categ_paint = Category.create({"name": "Paint TGT"})
        cls.categ_tools = Category.create({"name": "Tools TGT"})
        cls.categ_brushes = Category.create({"name": "Brushes TGT", "parent_id": cls.categ_tools.id})
        Product = cls.env["product.product"]
        cls.paint = Product.create(
            {
                "name": "Paint",
                "manufacturer_id": cls.manufacturer.id,
                "public_categ_ids": [(6, 0, cls.categ_paint.ids)],
            }
        )
        # in two categories: counts in both, but once in the overall target
        cls.brush = Product.create(
            {
                "name": "Brush",
                "manufacturer_id": cls.manufacturer.id,
                "public_categ_ids": [(6, 0, (cls.categ_paint | cls.categ_brushes).ids)],
            }
        )
        cls.other = Product.create({"name": "Other manufacturer"})

        cls._bill(cls.manufacturer, "2026-02-10", [(cls.paint, 10, 100), (cls.brush, 5, 20), (cls.other, 1, 999)])
        cls._bill(cls.manufacturer, "2026-05-10", [(cls.paint, 4, 100)])
        cls._bill(cls.manufacturer, "2026-05-20", [(cls.paint, 2, 100)], move_type="in_refund")
        cls._bill(cls.reseller, "2026-03-10", [(cls.paint, 50, 100)])
        cls._bill(cls.manufacturer, "2025-12-10", [(cls.paint, 50, 100)])
        cls._bill(cls.partner_a, "2026-02-15", [(cls.paint, 3, 150)], move_type="out_invoice")

        cls.target = cls.env["purchase.target"].create(
            {
                "manufacturer_id": cls.manufacturer.id,
                "year": 2026,
                "line_ids": [
                    (0, 0, {"quarter": "1", "target_value": 1000}),
                    (0, 0, {"quarter": "2", "target_value": 1000}),
                    (0, 0, {"quarter": "1", "public_categ_id": cls.categ_paint.id, "target_value": 500}),
                    (0, 0, {"quarter": "1", "public_categ_id": cls.categ_tools.id, "target_value": 200}),
                ],
            }
        )
        cls.env.flush_all()

    @classmethod
    def _bill(cls, partner, date, lines, move_type="in_invoice"):
        move = cls.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": date,
                "date": date,
                "invoice_line_ids": [
                    (0, 0, {"product_id": product.id, "quantity": qty, "price_unit": price, "tax_ids": []})
                    for product, qty, price in lines
                ],
            }
        )
        move.action_post()
        return move

    def _line(self, quarter, categ=None):
        return self.target.line_ids.filtered(
            lambda line: line.quarter == quarter
            and line.public_categ_id == (categ or self.env["product.public.category"])
        )

    def test_vendors_default_to_manufacturer(self):
        self.assertEqual(self.target.partner_ids, self.manufacturer)
        self.assertEqual(self.target.name, "Manufacturer TGT 2026")

    def test_overall_cumulated(self):
        q1 = self._line("1")
        # 10 x 100 + 5 x 20; the reseller, the other manufacturer and 2025 are left out
        self.assertAlmostEqual(q1.purchase_amount, 1100)
        self.assertAlmostEqual(q1.purchase_qty, 15)
        self.assertAlmostEqual(q1.purchase_ytd, 1100)
        self.assertAlmostEqual(q1.achieved_pct, 110)
        q2 = self._line("2")
        # 4 x 100 billed, 2 x 100 credited
        self.assertAlmostEqual(q2.purchase_amount, 200)
        self.assertAlmostEqual(q2.purchase_qty, 2)
        self.assertAlmostEqual(q2.target_ytd, 2000)
        self.assertAlmostEqual(q2.purchase_ytd, 1300)
        self.assertAlmostEqual(q2.remaining, 700)
        self.assertAlmostEqual(q2.achieved_pct, 65)

    def test_categories(self):
        self.assertAlmostEqual(self._line("1", self.categ_paint).purchase_amount, 1100)
        # the brush is in a child category of Tools
        self.assertAlmostEqual(self._line("1", self.categ_tools).purchase_amount, 100)
        self.assertAlmostEqual(self._line("1", self.categ_tools).achieved_pct, 50)

    def test_target_ytd_follows_sibling(self):
        q2 = self._line("2")
        self.assertAlmostEqual(q2.target_ytd, 2000)
        self._line("1").target_value = 1500
        self.assertAlmostEqual(q2.target_ytd, 2500)
        self.assertAlmostEqual(q2.remaining, 1200)

    def test_quantity_target(self):
        self.target.target_type = "qty"
        self.assertAlmostEqual(self._line("2").purchase_ytd, 17)

    def test_quantity_in_product_unit(self):
        """A bill line in dozens counts in the unit of the product (units)."""
        self.env.user.group_ids |= self.env.ref("uom.group_uom")
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.manufacturer.id,
                "invoice_date": "2026-08-10",
                "date": "2026-08-10",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.paint.id,
                            "quantity": 2,
                            "product_uom_id": self.env.ref("uom.product_uom_dozen").id,
                            "price_unit": 1200,
                            "tax_ids": [],
                        },
                    )
                ],
            }
        )
        move.action_post()
        self.target.write({"target_type": "qty", "line_ids": [(0, 0, {"quarter": "3", "target_value": 100})]})
        self.env.flush_all()
        q3 = self._line("3")
        self.assertAlmostEqual(q3.purchase_qty, 24)
        # 15 + 2 in the first half of the year, 24 in Q3
        self.assertAlmostEqual(q3.purchase_ytd, 41)

    def test_sales_on_same_products(self):
        q1 = self._line("1")
        self.assertAlmostEqual(q1.sale_amount, 450)
        self.assertAlmostEqual(q1.sale_qty, 3)
        self.assertAlmostEqual(self._line("2").sale_ytd, 450)

    def test_drill_down(self):
        action = self._line("1").action_view_purchases()
        bill_lines = self.env["account.move.line"].search(action["domain"])
        self.assertEqual(bill_lines.product_id, self.paint | self.brush)
        action = self._line("1").action_view_sales()
        self.assertEqual(self.env["sale.margin.report"].search(action["domain"]).product_id, self.paint)

    def test_year_range(self):
        with self.assertRaises(ValidationError):
            self.target.year = 20260

    def test_unique_quarter_category(self):
        with self.assertRaises(ValidationError):
            self.target.line_ids = [(0, 0, {"quarter": "1", "target_value": 5})]

    def test_purchase_user_without_accounting(self):
        """A purchase user follows the targets: purchases yes, sales and bill lines no."""
        user = self.env["res.users"].create(
            {
                "name": "Buyer TGT",
                "login": "buyer_tgt",
                "company_id": self.env.company.id,
                "company_ids": [Command.set(self.env.company.ids)],
                "group_ids": [Command.set(self.env.ref("purchase.group_purchase_user").ids)],
            }
        )
        line = self._line("1").with_user(user)
        self.assertAlmostEqual(line.purchase_ytd, 1100)
        with self.assertRaises(AccessError):
            line.read(["sale_amount"])
        with self.assertRaises(AccessError):
            line.target_id.write({"year": 2027})

    def test_other_company_bills_excluded(self):
        other_company = self.setup_other_company()["company"]
        self.env.user.company_ids |= other_company
        bill = (
            self.env["account.move"]
            .with_company(other_company)
            .create(
                {
                    "move_type": "in_invoice",
                    "partner_id": self.manufacturer.id,
                    "invoice_date": "2026-02-20",
                    "date": "2026-02-20",
                    "company_id": other_company.id,
                    "invoice_line_ids": [(0, 0, {"product_id": self.paint.id, "quantity": 7, "price_unit": 100})],
                }
            )
        )
        bill.action_post()
        self.env.flush_all()
        self.target.line_ids.invalidate_recordset()
        self.assertAlmostEqual(self._line("1").purchase_amount, 1100)
