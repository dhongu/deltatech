# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import io

from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductReorderingLimit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        Template = cls.env["product.template"]
        cls.tmpl_below = Template.create(
            {
                "name": "TEST Reorder Below",
                "default_code": "TRL-BELOW",
                "type": "consu",
                "is_storable": True,
                "total_minimum": 10.0,
                "total_maximum": 30.0,
            }
        )
        cls.tmpl_above = Template.create(
            {
                "name": "TEST Reorder Above",
                "default_code": "TRL-ABOVE",
                "type": "consu",
                "is_storable": True,
                "total_minimum": 5.0,
                "total_maximum": 8.0,
            }
        )
        cls.tmpl_no_limit = Template.create(
            {
                "name": "TEST Reorder No Limit",
                "type": "consu",
                "is_storable": True,
            }
        )
        Quant = cls.env["stock.quant"]
        Quant._update_available_quantity(cls.tmpl_below.product_variant_id, cls.stock_location, 4.0)
        # Stock in a non-internal location must be ignored
        Quant._update_available_quantity(cls.tmpl_below.product_variant_id, cls.customer_location, 100.0)
        Quant._update_available_quantity(cls.tmpl_above.product_variant_id, cls.stock_location, 12.0)

    # ------------------------------------------------------------------
    # product.template fields
    # ------------------------------------------------------------------
    def test_default_limits(self):
        self.assertEqual(self.tmpl_no_limit.total_minimum, 0.0)
        self.assertEqual(self.tmpl_no_limit.total_maximum, 0.0)

    def test_form_limits(self):
        with Form(self.env["product.template"]) as form:
            form.name = "TEST Reorder Form"
            form.total_minimum = 3.0
            form.total_maximum = 7.0
        template = form.save()
        self.assertEqual(template.total_minimum, 3.0)
        self.assertEqual(template.total_maximum, 7.0)
        self.assertTrue(template.is_below_min)

    def test_compute_is_below_min(self):
        self.assertEqual(self.tmpl_below.qty_available, 4.0)
        self.assertTrue(self.tmpl_below.is_below_min)
        self.assertFalse(self.tmpl_above.is_below_min)
        self.assertFalse(self.tmpl_no_limit.is_below_min)

    def test_compute_reacts_to_minimum_change(self):
        self.tmpl_above.total_minimum = 20.0
        self.assertTrue(self.tmpl_above.is_below_min)
        self.tmpl_below.total_minimum = 0.0
        self.assertFalse(self.tmpl_below.is_below_min)

    def test_search_is_below_min_true(self):
        templates = self.env["product.template"].search([("is_below_min", "=", True)])
        self.assertIn(self.tmpl_below, templates)
        self.assertNotIn(self.tmpl_above, templates)
        self.assertNotIn(self.tmpl_no_limit, templates)

    def test_search_is_below_min_false(self):
        templates = self.env["product.template"].search([("is_below_min", "=", False)])
        self.assertNotIn(self.tmpl_below, templates)
        self.assertIn(self.tmpl_above, templates)
        self.assertIn(self.tmpl_no_limit, templates)
        templates = self.env["product.template"].search([("is_below_min", "!=", True)])
        self.assertNotIn(self.tmpl_below, templates)
        self.assertIn(self.tmpl_above, templates)

    def test_search_filter_from_view(self):
        """The 'Below Minimum' filter domain works on the search view."""
        templates = self.env["product.template"].search([("is_below_min", "=", True), ("name", "like", "TEST Reorder")])
        self.assertEqual(templates, self.tmpl_below)

    def test_search_without_stock(self):
        template = self.env["product.template"].create(
            {"name": "TEST Reorder Empty", "type": "consu", "is_storable": True, "total_minimum": 1.0}
        )
        self.assertTrue(template.is_below_min)
        self.assertIn(template, self.env["product.template"].search([("is_below_min", "=", True)]))

    def test_search_variants_aggregated(self):
        attribute = self.env["product.attribute"].create(
            {
                "name": "TEST Reorder Size",
                "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "M"})],
            }
        )
        template = self.env["product.template"].create(
            {
                "name": "TEST Reorder Variants",
                "type": "consu",
                "is_storable": True,
                "total_minimum": 10.0,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, attribute.value_ids.ids)]})
                ],
            }
        )
        variants = template.product_variant_ids
        self.assertEqual(len(variants), 2)
        Quant = self.env["stock.quant"]
        Quant._update_available_quantity(variants[0], self.stock_location, 6.0)
        self.assertTrue(template.is_below_min)
        self.assertIn(template, self.env["product.template"].search([("is_below_min", "=", True)]))
        Quant._update_available_quantity(variants[1], self.stock_location, 6.0)
        self.env.invalidate_all()
        self.assertFalse(template.is_below_min)
        self.assertNotIn(template, self.env["product.template"].search([("is_below_min", "=", True)]))

    def test_search_unsupported_operator(self):
        Template = self.env["product.template"]
        with self.assertRaises(NotImplementedError):
            Template._search_is_below_min("=", True)
        with self.assertRaises(NotImplementedError):
            Template._search_is_below_min("in", [False])

    def test_search_direct_not_in(self):
        domain = self.env["product.template"]._search_is_below_min("not in", [True])
        self.assertEqual(domain[0][0], "id")
        self.assertEqual(domain[0][1], "not in")
        self.assertIn(self.tmpl_below.id, domain[0][2])

    # ------------------------------------------------------------------
    # wizard
    # ------------------------------------------------------------------
    def _wizard(self, **ctx):
        return self.env["product.reordering.report.wizard"].with_context(**ctx).create({})

    def test_wizard_no_selection(self):
        wizard = self._wizard()
        with self.assertRaises(UserError):
            wizard.action_generate_report()

    def test_wizard_other_model(self):
        wizard = self._wizard(active_model="res.partner", active_ids=[self.tmpl_below.id])
        self.assertFalse(wizard._get_products())
        with self.assertRaises(UserError):
            wizard.action_generate_report()

    def test_wizard_empty_active_ids(self):
        wizard = self._wizard(active_model="product.template", active_ids=None)
        self.assertFalse(wizard._get_products())
        with self.assertRaises(UserError):
            wizard.action_generate_report()

    def test_wizard_generate_report(self):
        products = self.tmpl_below | self.tmpl_above | self.tmpl_no_limit
        wizard = self._wizard(active_model="product.template", active_ids=products.ids)
        self.assertEqual(wizard._get_products(), products)
        action = wizard.action_generate_report()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "product.reordering.report.wizard")
        self.assertEqual(action["res_id"], wizard.id)
        self.assertEqual(action["target"], "new")
        self.assertEqual(wizard.filename, "Reordering_Report.xlsx")
        self.assertTrue(wizard.file)

        try:
            import openpyxl
        except ImportError:
            return
        content = base64.b64decode(wizard.file)
        sheet = openpyxl.load_workbook(io.BytesIO(content)).active
        rows = list(sheet.iter_rows(values_only=True))
        self.assertEqual(sheet.title, "Reordering Report")
        self.assertEqual(list(rows[0]), ["Default Code", "Name", "Under Quantity", "Required Quantity", "Range"])
        self.assertEqual(len(rows), 4)
        by_name = {row[1]: row for row in rows[1:]}
        below = by_name[self.tmpl_below.display_name]
        self.assertEqual(below[0], "TRL-BELOW")
        self.assertEqual(below[2], 6.0)
        self.assertEqual(below[3], 26.0)
        self.assertEqual(below[4], "10.0 -> 30.0")
        above = by_name[self.tmpl_above.display_name]
        self.assertEqual(above[2], 0.0)
        self.assertEqual(above[3], 0.0)
        no_limit = by_name[self.tmpl_no_limit.display_name]
        self.assertIn(no_limit[0], ("", None))
        self.assertEqual(no_limit[4], "0.0 -> 0.0")
