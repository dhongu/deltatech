from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPackagingMaterial(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a.country_id = cls.env.ref("base.us")
        cls.product_a.standard_price = 0.0
        # the product is packed differently by the vendor and on shipping: more plastic
        # on purchase, wood only on sale and paper only on purchase
        cls.product_a.product_tmpl_id.packaging_material_ids = [
            Command.create({"material_type": "plastic", "qty_sale": 1.0, "qty_purchase": 3.0}),
            Command.create({"material_type": "wood", "qty_sale": 0.5, "qty_purchase": 0.0}),
            Command.create({"material_type": "glass", "qty_sale": 0.25, "qty_purchase": 0.25}),
            Command.create({"material_type": "paper", "qty_sale": 0.0, "qty_purchase": 2.0}),
        ]

    def _create_invoice(self, quantity=2.0, move_type="out_invoice"):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": quantity,
                            "price_unit": 100.0,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )

    def test_post_computes_packaging_materials(self):
        invoice = self._create_invoice()

        invoice.action_post()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 2.0, "wood": 1.0, "glass": 0.5},
        )

    def test_post_recomputes_existing_packaging_materials(self):
        invoice = self._create_invoice()
        invoice.refresh_packaging_material()
        invoice.invoice_line_ids.quantity = 4.0

        invoice.action_post()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 4.0, "wood": 2.0, "glass": 1.0},
        )

    def test_refresh_replaces_previous_values(self):
        invoice = self._create_invoice()
        invoice.refresh_packaging_material()
        invoice.invoice_line_ids.quantity = 4.0

        invoice.refresh_packaging_material()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 4.0, "wood": 2.0, "glass": 1.0},
        )

    def test_report_aggregates_invoices_and_supports_all_material_types(self):
        invoices = self._create_invoice(2.0) | self._create_invoice(3.0)
        report = self.env["packaging.report.material"].with_context(active_ids=invoices.ids).create({})

        action = report.do_report()

        quantities = {line.material_type: line.qty for line in report.line_ids}
        self.assertEqual(
            quantities,
            {"plastic": 5.0, "wood": 2.5, "glass": 1.25},
        )
        self.assertEqual(report.state, "get")
        self.assertEqual(action["res_id"], report.id)

    def test_manual_quantity_unsets_the_automatic_update(self):
        invoice = self._create_invoice()
        invoice.refresh_packaging_material()
        self.assertTrue(invoice.packaging_material_auto)

        invoice.packaging_material_ids.filtered(lambda line: line.material_type == "plastic").qty = 7.0

        self.assertFalse(invoice.packaging_material_auto)

    def test_deleting_a_quantity_unsets_the_automatic_update(self):
        invoice = self._create_invoice()
        invoice.refresh_packaging_material()

        invoice.packaging_material_ids.filtered(lambda line: line.material_type == "wood").unlink()

        self.assertFalse(invoice.packaging_material_auto)

    def test_post_keeps_manual_quantities(self):
        invoice = self._create_invoice()
        invoice.refresh_packaging_material()
        invoice.packaging_material_ids.filtered(lambda line: line.material_type == "glass").unlink()
        invoice.packaging_material_ids.filtered(lambda line: line.material_type == "plastic").qty = 7.0

        invoice.action_post()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 7.0, "wood": 1.0},
            "the quantities set by hand survive the validation of the invoice",
        )
        self.assertFalse(invoice.packaging_material_auto)

    def test_refresh_takes_the_invoice_back_under_automatic_update(self):
        invoice = self._create_invoice()
        invoice.refresh_packaging_material()
        invoice.packaging_material_ids.filtered(lambda line: line.material_type == "plastic").qty = 7.0

        invoice.refresh_packaging_material()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(quantities, {"plastic": 2.0, "wood": 1.0, "glass": 0.5})
        self.assertTrue(invoice.packaging_material_auto)

    def test_refresh_does_not_unset_the_automatic_update(self):
        invoice = self._create_invoice()

        invoice.refresh_packaging_material()

        self.assertTrue(
            invoice.packaging_material_auto,
            "the computation itself is not a manual edit",
        )

    def test_vendor_bill_uses_the_purchase_quantities(self):
        bill = self._create_invoice(move_type="in_invoice")

        bill.action_post()

        quantities = {line.material_type: line.qty for line in bill.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 6.0, "glass": 0.5, "paper": 4.0},
            "the bill is packed as bought: no wood, and the paper of the vendor packaging",
        )

    def test_customer_invoice_uses_the_sale_quantities(self):
        invoice = self._create_invoice()

        invoice.action_post()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 2.0, "wood": 1.0, "glass": 0.5},
            "the paper is only used by the vendor, so it is not reported on the sale",
        )

    def test_refund_follows_the_direction_of_the_invoice_it_corrects(self):
        refund = self._create_invoice(move_type="in_refund")

        refund.action_post()

        quantities = {line.material_type: line.qty for line in refund.packaging_material_ids}
        self.assertEqual(quantities, {"plastic": 6.0, "glass": 0.5, "paper": 4.0})


@tagged("post_install", "-at_install")
class TestPackagingMaterialCategory(AccountTestInvoicingCommon):
    """The materials of a product default to the ones of its category."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a.country_id = cls.env.ref("base.us")
        cls.product_a.standard_price = 0.0
        cls.parent_category = cls.env["product.category"].create({"name": "Packed goods"})
        cls.category = cls.env["product.category"].create({"name": "Boxed goods", "parent_id": cls.parent_category.id})
        cls.parent_category.packaging_material_ids = [
            Command.create({"material_type": "paper", "qty_sale": 4.0, "qty_purchase": 6.0}),
        ]
        cls.product_a.product_tmpl_id.categ_id = cls.category

    def _create_invoice(self, quantity=2.0, move_type="out_invoice"):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": quantity,
                            "price_unit": 100.0,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )

    def test_a_material_belongs_to_a_product_or_to_a_category(self):
        from psycopg2.errors import CheckViolation

        for vals in (
            {"material_type": "paper", "qty_sale": 1.0},
            {
                "material_type": "paper",
                "qty_sale": 1.0,
                "categ_id": self.category.id,
                "product_tmpl_id": self.product_a.product_tmpl_id.id,
            },
        ):
            with self.assertRaises(CheckViolation), self.cr.savepoint():
                self.env["packaging.product.material"].create(vals)

    def test_product_without_materials_uses_the_ones_of_its_category(self):
        self.category.packaging_material_ids = [
            Command.create({"material_type": "plastic", "qty_sale": 1.0, "qty_purchase": 3.0}),
        ]

        materials = self.product_a.product_tmpl_id._get_packaging_materials()

        self.assertEqual(materials.material_type, "plastic")
        self.assertEqual(materials.categ_id, self.category)

    def test_category_without_materials_falls_back_to_its_parent(self):
        materials = self.product_a.product_tmpl_id._get_packaging_materials()

        self.assertEqual(materials.material_type, "paper")
        self.assertEqual(
            materials.categ_id,
            self.parent_category,
            "the configuration of a parent covers the subcategories that have none",
        )

    def test_materials_of_the_product_take_precedence_over_the_category(self):
        self.category.packaging_material_ids = [
            Command.create({"material_type": "plastic", "qty_sale": 1.0}),
        ]
        self.product_a.product_tmpl_id.packaging_material_ids = [
            Command.create({"material_type": "wood", "qty_sale": 0.5, "qty_purchase": 0.5}),
        ]

        materials = self.product_a.product_tmpl_id._get_packaging_materials()

        self.assertEqual(materials.material_type, "wood")
        self.assertFalse(
            self.product_a.product_tmpl_id.inherited_packaging_material_ids,
            "a product configured on its own inherits nothing",
        )

    def test_invoice_computes_the_inherited_quantities(self):
        invoice = self._create_invoice(quantity=2.0)

        invoice.action_post()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(quantities, {"paper": 8.0})

    def test_vendor_bill_uses_the_inherited_purchase_quantities(self):
        bill = self._create_invoice(quantity=2.0, move_type="in_invoice")

        bill.action_post()

        quantities = {line.material_type: line.qty for line in bill.packaging_material_ids}
        self.assertEqual(quantities, {"paper": 12.0})

    def test_changing_the_category_changes_the_materials_of_the_product(self):
        other_category = self.env["product.category"].create(
            {
                "name": "Crated goods",
                "packaging_material_ids": [Command.create({"material_type": "wood", "qty_sale": 2.0})],
            }
        )

        self.product_a.product_tmpl_id.categ_id = other_category

        self.assertEqual(
            self.product_a.product_tmpl_id._get_packaging_materials().material_type,
            "wood",
            "the materials follow the category, nothing is copied on the product",
        )

    def test_inherited_materials_are_shown_on_the_product(self):
        self.assertEqual(
            self.product_a.product_tmpl_id.inherited_packaging_material_ids.material_type,
            "paper",
        )

    def test_a_product_can_opt_out_of_the_materials_of_its_category(self):
        self.product_a.product_tmpl_id.packaging_material_no_inherit = True

        self.assertFalse(
            self.product_a.product_tmpl_id._get_packaging_materials(),
            "a product packed in nothing stays empty inside a category that is packed",
        )
        self.assertFalse(self.product_a.product_tmpl_id.inherited_packaging_material_ids)

    def test_opting_out_reports_no_material_on_the_invoice(self):
        self.product_a.product_tmpl_id.packaging_material_no_inherit = True
        invoice = self._create_invoice(quantity=2.0)

        invoice.action_post()

        self.assertFalse(invoice.packaging_material_ids)

    def test_materials_of_the_product_are_used_even_when_opting_out(self):
        self.product_a.product_tmpl_id.packaging_material_no_inherit = True
        self.product_a.product_tmpl_id.packaging_material_ids = [
            Command.create({"material_type": "wood", "qty_sale": 0.5, "qty_purchase": 0.5}),
        ]

        materials = self.product_a.product_tmpl_id._get_packaging_materials()

        self.assertEqual(
            materials.material_type,
            "wood",
            "the option only stops the inheritance, it does not clear the product",
        )
