# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestUpdateProductStatistics(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )

    def test_update_statistics(self):
        self.env["product.template"]._cron_update_statistics()

    def test_template_totals_use_fresh_variant_values(self):
        """The template sum must not read stale variant counters (#3504)."""
        template = self.product_a.product_tmpl_id
        # Stale values, as left by a variant job that has not run yet.
        self.product_a.write({"visit_count": 99, "sales_count2": 99})
        visitor = self.env["website.visitor"].create({"access_token": "f9d2b14a3c3e4b6d8e2a1c5b7d9e0f12"})
        self.env["website.track"].create(
            [{"visitor_id": visitor.id, "product_id": self.product_a.id} for _i in range(3)]
        )

        template._update_statistics()

        self.assertEqual(self.product_a.visit_count, 3)
        self.assertEqual(self.product_a.sales_count2, 0)
        self.assertEqual(template.visit_count, 3)
        self.assertEqual(template.sales_count2, 0)
