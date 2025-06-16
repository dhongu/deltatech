# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError

from .test_common import TestCommon


class TestAccountMoveLine(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_a = cls.env["res.partner"].create(
            {
                "name": "Test Partner A",
            }
        )
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test Product A",
                "type": "product",
                "valuation_class_id": cls.valuation_class.id,
            }
        )

        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Test Sale Journal",
                "code": "TSJ1",
                "type": "sale",
                "company_id": cls.env.company.id,
            }
        )
        # Create an account modifier

        cls.rule_receipt = cls.env["product.account.determination"].create(
            {
                "transaction_key": "stock_income",
                "valuation_class_id": cls.valuation_class.id,
                "valuation_area_id": cls.valuation_area.id,
                "company_id": cls.env.company.id,
                "acc_src_id": cls.account_src.id,
                "acc_dest_id": cls.account_dest.id,
                "acc_valuation_id": cls.account_valuation.id,
            }
        )

        cls.out_invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "date": "2017-01-01",
                "invoice_date": "2017-01-01",
                "partner_id": cls.partner_a.id,
                "currency_id": cls.env.company.currency_id.id,
                "journal_id": cls.sale_journal.id,
                "company_id": cls.env.company.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_a.id,
                            "product_uom_id": cls.product_a.uom_id.id,
                            "account_id": cls.account_src.id,
                            "price_unit": 23.98,
                            "quantity": 1.0,
                            "tax_ids": [],
                        },
                    )
                ],
            }
        )

        cls.account_move_line = cls.out_invoice.line_ids.filtered(lambda line: line.display_type == "product")

    def test_get_valuation_area_defined(self):
        """Test _get_valuation_area when valuation_area_id is explicitly defined."""
        valuation_area = self.account_move_line._get_valuation_area()
        self.assertEqual(
            valuation_area.id, self.valuation_area.id, "The valuation area should match the explicitly defined one."
        )

    def test_compute_account_id_with_valid_product(self):
        """
        Test _compute_account_id with a valid product that has a defined
        valuation class and valuation area.
        """
        self.account_move_line._compute_account_id()
        self.assertEqual(
            self.account_move_line.account_id,
            self.account_dest,
            "The account_id should match the source account defined in the rule.",
        )

    def test_get_valuation_area_inherited_from_company(self):
        """Test _get_valuation_area when valuation_area_id is inherited from the company."""
        self.account_move_line.valuation_area_id = False
        self.env.company.valuation_area_id = self.valuation_area

        valuation_area = self.account_move_line._get_valuation_area()
        self.assertEqual(
            valuation_area.id,
            self.valuation_area.id,
            "The valuation area should match the one inherited from the company.",
        )

    def test_get_valuation_area_undefined_raises_error(self):
        """Test _get_valuation_area raises UserError when no valuation area is defined."""
        self.account_move_line.valuation_area_id = False
        self.env.company.valuation_area_id = False

        with self.assertRaises(UserError):
            self.account_move_line._get_valuation_area()
