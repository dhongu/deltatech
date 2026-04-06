# ©  2008-2021 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestAccountInvoiceReport(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a partner
        self.partner_a = self.env["res.partner"].create(
            {
                "name": "Test Partner A",
            }
        )

        # Create an account journal
        self.journal = self.env["account.journal"].create(
            {
                "name": "Test Journal",
                "type": "sale",
                "code": "TJ",
            }
        )

        # Create an account move
        self.account_move = self.env["account.move"].create(
            {
                "partner_id": self.partner_a.id,
                "journal_id": self.journal.id,
                "invoice_date": "2022-01-01",
                "move_type": "out_invoice",
            }
        )

    def test_manufacturer_field(self):
        self.env["account.invoice.report"].search([("move_id", "=", self.account_move.id)], limit=1)

        # Check the manufacturer field


class TestProductTemplate(TransactionCase):
    def test_product_template_fields(self):
        # Create a test record for product.template
        partner_b = self.env["res.partner"].create(
            {
                "name": "Test Partner B",
            }
        )
        product_template = self.env["product.template"].create(
            {
                "name": "Test Product Template",
                "dimensions": "10x5x3",
                "shelf_life": 2.5,
                "uom_shelf_life": self.env.ref("uom.product_uom_unit").id,  # Example unit of measure
                "manufacturer": partner_b.id,  # Example manufacturer
            }
        )

        # Check that fields are correctly added
        self.assertTrue(hasattr(product_template, "dimensions"), "Dimensions field is not added to product.template")
        self.assertTrue(hasattr(product_template, "shelf_life"), "Shelf Life field is not added to product.template")
        self.assertTrue(
            hasattr(product_template, "uom_shelf_life"), "UoM Shelf Life field is not added to product.template"
        )
        self.assertTrue(
            hasattr(product_template, "manufacturer"), "Manufacturer field is not added to product.template"
        )


class TestResPartner(TransactionCase):
    def test_res_partner_fields(self):
        # Create a test record for res.partner
        res_partner = self.env["res.partner"].create({"name": "Test Manufacturer", "is_manufacturer": True})

        # Check that is_manufacturer field is correctly added
        self.assertTrue(hasattr(res_partner, "is_manufacturer"), "Is Manufacturer field is not added to res.partner")
        self.assertTrue(res_partner.is_manufacturer, "Is Manufacturer field value should be True for test record")
