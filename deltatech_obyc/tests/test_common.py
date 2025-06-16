# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test accounts
        cls.account_src = cls.env["account.account"].create(
            {
                "name": "Test Source Account",
                "code": "TSA001",
                "account_type": "asset_current",
            }
        )
        cls.account_dest = cls.env["account.account"].create(
            {
                "name": "Test Destination Account",
                "code": "TDA001",
                "account_type": "asset_current",
            }
        )
        cls.account_valuation = cls.env["account.account"].create(
            {
                "name": "Test Valuation Account",
                "code": "TVA001",
                "account_type": "asset_current",
            }
        )

        # Create a valuation class
        cls.valuation_class = cls.env["product.valuation.class"].create(
            {
                "name": "Test Class",
                "code": "TC",
            }
        )

        cls.stock_journal = cls.env["account.journal"].create(
            {
                "name": "Test Stock Journal",
                "code": "TSJ",
                "type": "general",
                "company_id": cls.env.company.id,
            }
        )

        # Create a valuation area
        cls.valuation_area = cls.env["valuation.area"].create(
            {
                "name": "Test Area",
                "code": "TA",
                "stock_journal_id": cls.stock_journal.id,
            }
        )

        cls.env.company.write(
            {
                "valuation_area_id": cls.valuation_area.id,
            }
        )

        # Create an account modifier
        cls.account_modifier = cls.env["account.modifier"].create(
            {
                "name": "Test Modifier",
                "code": "TM",
            }
        )

        # Create product category
        cls.product_category = cls.env["product.category"].create(
            {
                "name": "Test Category",
            }
        )

        # Create test product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "categ_id": cls.product_category.id,
                "valuation_class_id": cls.valuation_class.id,
            }
        )

        # Assign valuation area to company
        cls.env.company.write(
            {
                "valuation_area_id": cls.valuation_area.id,
            }
        )
