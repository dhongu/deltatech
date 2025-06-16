# © 2025 Deltatech
# See README.rst file on addons root folder for license details


from odoo.exceptions import RedirectWarning

from .test_common import TestCommon


class TestOBYCAccountDetermination(TestCommon):
    def test_01_account_determination_creation(self):
        """Test creating account determination rules"""
        # Create a rule for stock_receipt
        rule_receipt = self.env["product.account.determination"].create(
            {
                "transaction_key": "stock_receipt",
                "valuation_class_id": self.valuation_class.id,
                "valuation_area_id": self.valuation_area.id,
                "account_modifier_id": self.account_modifier.id,
                "company_id": self.env.company.id,
                "acc_src_id": self.account_src.id,
                "acc_dest_id": self.account_dest.id,
                "acc_valuation_id": self.account_valuation.id,
            }
        )

        self.assertEqual(rule_receipt.transaction_key, "stock_receipt")
        self.assertEqual(rule_receipt.acc_src_id, self.account_src)
        self.assertEqual(rule_receipt.acc_dest_id, self.account_dest)
        self.assertEqual(rule_receipt.acc_valuation_id, self.account_valuation)

        # Create a rule for stock_delivery
        rule_delivery = self.env["product.account.determination"].create(
            {
                "transaction_key": "stock_delivery",
                "valuation_class_id": self.valuation_class.id,
                "valuation_area_id": self.valuation_area.id,
                "account_modifier_id": self.account_modifier.id,
                "company_id": self.env.company.id,
                "acc_src_id": self.account_dest.id,  # Reversed for delivery
                "acc_dest_id": self.account_src.id,  # Reversed for delivery
                "acc_valuation_id": self.account_valuation.id,
            }
        )

        self.assertEqual(rule_delivery.transaction_key, "stock_delivery")
        self.assertEqual(rule_delivery.acc_src_id, self.account_dest)
        self.assertEqual(rule_delivery.acc_dest_id, self.account_src)
        self.assertEqual(rule_delivery.acc_valuation_id, self.account_valuation)

    def test_02_get_rule_account(self):
        """Test getting account determination rule"""
        # Create a rule for stock_receipt
        rule_receipt = self.env["product.account.determination"].create(
            {
                "transaction_key": "stock_receipt",
                "valuation_class_id": self.valuation_class.id,
                "valuation_area_id": self.valuation_area.id,
                "account_modifier_id": self.account_modifier.id,
                "company_id": self.env.company.id,
                "acc_src_id": self.account_src.id,
                "acc_dest_id": self.account_dest.id,
                "acc_valuation_id": self.account_valuation.id,
            }
        )

        # Get the rule using _get_rule_account method
        found_rule = self.env["product.account.determination"]._get_rule_account(
            valuation_area=self.valuation_area,
            valuation_class=self.valuation_class,
            transaction_key="stock_receipt",
            account_modifier=self.account_modifier,
            company=self.env.company,
        )

        self.assertEqual(found_rule.id, rule_receipt.id)
        self.assertEqual(found_rule.acc_src_id, self.account_src)
        self.assertEqual(found_rule.acc_dest_id, self.account_dest)
        self.assertEqual(found_rule.acc_valuation_id, self.account_valuation)

    def test_03_missing_rule_error(self):
        """Test error when rule is missing"""
        # Try to get a non-existent rule
        with self.assertRaises(RedirectWarning):
            self.env["product.account.determination"]._get_rule_account(
                valuation_area=self.valuation_area,
                valuation_class=self.valuation_class,
                transaction_key="internal_transfer",  # No rule for this
                account_modifier=self.account_modifier,
                company=self.env.company,
            )

    def test_04_multiple_transaction_keys(self):
        """Test creating rules for different transaction keys"""
        # Create rules for different transaction keys
        transaction_keys = [
            "stock_valuation",
            "stock_receipt",
            "return_to_supplier",
            "stock_delivery",
            "return_from_customer",
            "stock_income",
            "internal_transfer",
            "inventory_adjustment_plus",
            "inventory_adjustment_minus",
            "production_issue",
            "production_receipt",
        ]

        for key in transaction_keys:
            rule = self.env["product.account.determination"].create(
                {
                    "transaction_key": key,
                    "valuation_class_id": self.valuation_class.id,
                    "valuation_area_id": self.valuation_area.id,
                    "account_modifier_id": self.account_modifier.id,
                    "company_id": self.env.company.id,
                    "acc_src_id": self.account_src.id,
                    "acc_dest_id": self.account_dest.id,
                    "acc_valuation_id": self.account_valuation.id,
                }
            )

            self.assertEqual(rule.transaction_key, key)
            self.assertEqual(rule.acc_src_id, self.account_src)
            self.assertEqual(rule.acc_dest_id, self.account_dest)
            self.assertEqual(rule.acc_valuation_id, self.account_valuation)

            # Verify rule retrieval
            found_rule = self.env["product.account.determination"]._get_rule_account(
                valuation_area=self.valuation_area,
                valuation_class=self.valuation_class,
                transaction_key=key,
                account_modifier=self.account_modifier,
                company=self.env.company,
            )

            self.assertEqual(found_rule.id, rule.id)

    def test_05_display_name_computation(self):
        """Test the display name computation"""
        rule = self.env["product.account.determination"].create(
            {
                "transaction_key": "stock_receipt",
                "valuation_class_id": self.valuation_class.id,
                "valuation_area_id": self.valuation_area.id,
                "account_modifier_id": self.account_modifier.id,
                "company_id": self.env.company.id,
                "acc_src_id": self.account_src.id,
                "acc_dest_id": self.account_dest.id,
                "acc_valuation_id": self.account_valuation.id,
            }
        )

        rule._compute_display_name()
        expected_name = (
            f"stock_receipt - {self.valuation_class.name} - {self.valuation_area.name} - {self.account_modifier.name}"
        )
        self.assertEqual(rule.display_name, expected_name)

        # Test without account modifier
        rule_no_modifier = self.env["product.account.determination"].create(
            {
                "transaction_key": "stock_delivery",
                "valuation_class_id": self.valuation_class.id,
                "valuation_area_id": self.valuation_area.id,
                "account_modifier_id": False,
                "company_id": self.env.company.id,
                "acc_src_id": self.account_src.id,
                "acc_dest_id": self.account_dest.id,
                "acc_valuation_id": self.account_valuation.id,
            }
        )

        rule_no_modifier._compute_display_name()
        expected_name_no_modifier = f"stock_delivery - {self.valuation_class.name} - {self.valuation_area.name} - None"
        self.assertEqual(rule_no_modifier.display_name, expected_name_no_modifier)

    def test_06_display_area_name_computation(self):
        """Test the display name computation for valuation area"""
        self.valuation_area._compute_display_name()
        expected_display_name = f"[{self.valuation_area.code}] {self.valuation_area.name}"
        self.assertEqual(self.valuation_area.display_name, expected_display_name)

        # Test with a different code
        self.valuation_area.code = "NEW_CODE"
        self.valuation_area._compute_display_name()
        expected_display_name_updated = f"[{self.valuation_area.code}] {self.valuation_area.name}"
        self.assertEqual(self.valuation_area.display_name, expected_display_name_updated)

    def test_07_display_class_name_computation(self):
        """Test the display name computation for valuation class"""
        self.valuation_class._compute_display_name()
        expected_display_name = f"[{self.valuation_class.code}] {self.valuation_class.name}"
        self.assertEqual(self.valuation_class.display_name, expected_display_name)

        # Test with a different code
        self.valuation_class.code = "NEW_CLASS_CODE"
        self.valuation_class._compute_display_name()
        expected_display_name_updated = f"[{self.valuation_class.code}] {self.valuation_class.name}"
        self.assertEqual(self.valuation_class.display_name, expected_display_name_updated)

    def test_08_display_modifier_name_computation(self):
        """Test the display name computation for account modifier"""
        self.account_modifier._compute_display_name()
        expected_display_name = f"[{self.account_modifier.code}] {self.account_modifier.name}"
        self.assertEqual(self.account_modifier.display_name, expected_display_name)

        # Test with a different code
        self.account_modifier.code = "NEW_MODIFIER_CODE"
        self.account_modifier._compute_display_name()
        expected_display_name_updated = f"[{self.account_modifier.code}] {self.account_modifier.name}"
        self.assertEqual(self.account_modifier.display_name, expected_display_name_updated)

    def test_09_account_determination_with_product_template(self):
        """Test account determination with product template"""
        # Create a product template with valuation class
        product_template = self.env["product.template"].create(
            {
                "name": "Test Product Template",
                "valuation_class_id": self.valuation_class.id,
                "categ_id": self.product_category.id,
            }
        )

        rule = self.env["product.account.determination"].create(
            {
                "transaction_key": "stock_receipt",
                "valuation_class_id": self.valuation_class.id,
                "valuation_area_id": self.valuation_area.id,
                "account_modifier_id": self.account_modifier.id,
                "company_id": self.env.company.id,
                "acc_src_id": self.account_src.id,
                "acc_dest_id": self.account_dest.id,
                "acc_valuation_id": self.account_valuation.id,
            }
        )

        # Get product accounts with transaction key
        self.env.context = dict(
            self.env.context,
            transaction_key="stock_receipt",
            valuation_area=self.valuation_area,
            account_modifier=self.account_modifier,
        )
        accounts = product_template.get_product_accounts()

        self.assertTrue(accounts["stock_valuation"])
        self.assertTrue(accounts["income"])
        self.assertTrue(accounts["expense"])
        self.assertTrue(accounts["stock_input"])
        self.assertTrue(accounts["stock_output"])

        # Check if the accounts match the created rule
        rule = self.env["product.account.determination"]._get_rule_account(
            valuation_area=self.valuation_area,
            valuation_class=product_template.valuation_class_id,
            transaction_key="stock_receipt",
            account_modifier=self.account_modifier,
            company=self.env.company,
        )

        self.assertEqual(accounts["stock_valuation"], rule.acc_valuation_id.id)
        self.assertEqual(accounts["income"], rule.acc_src_id.id)
        self.assertEqual(accounts["expense"], rule.acc_dest_id.id)
        self.assertEqual(accounts["stock_input"], rule.acc_src_id.id)
        self.assertEqual(accounts["stock_output"], rule.acc_dest_id.id)
