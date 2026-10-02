from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestProductUniqueCode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login="unique_code_user", groups="base.group_user")
        # sudo() keeps env.user, so the duplicate-code group is evaluated for the test user
        cls.Product = cls.env["product.product"].with_user(cls.user).sudo()
        cls.Template = cls.env["product.template"].with_user(cls.user).sudo()
        cls.product = cls.Product.create({"name": "Unique A", "default_code": "UQ-A", "barcode": "UQ-BAR-A"})

    def test_duplicate_default_code_on_create(self):
        with self.assertRaises(ValidationError):
            self.Product.create({"name": "Unique B", "default_code": "UQ-A"})

    def test_duplicate_barcode_on_template_create(self):
        with self.assertRaises(ValidationError):
            self.Template.create({"name": "Unique B", "barcode": "UQ-BAR-A"})

    def test_duplicate_with_archived_product(self):
        self.product.active = False
        with self.assertRaises(ValidationError):
            self.Product.create({"name": "Unique B", "default_code": "UQ-A"})

    def test_duplicate_on_write(self):
        other = self.Product.create({"name": "Unique B", "default_code": "UQ-B"})
        with self.assertRaises(ValidationError):
            other.write({"default_code": "UQ-A"})
        with self.assertRaises(ValidationError):
            other.product_tmpl_id.write({"default_code": "UQ-A"})

    def test_unchanged_historical_duplicate_allows_cleanup(self):
        # a historical duplicate (created by a privileged user) does not block
        # unrelated changes, archiving or fixing the code
        dup = self.env["product.product"].create({"name": "Dup", "default_code": "UQ-A"})
        dup = dup.with_user(self.user).sudo()
        dup.write({"name": "Dup renamed"})
        dup.product_tmpl_id.write({"description": "cleanup"})
        dup.write({"active": False})
        dup.write({"default_code": "UQ-A-OLD"})
        self.assertEqual(dup.default_code, "UQ-A-OLD")
        with self.assertRaises(ValidationError):
            dup.write({"default_code": "UQ-A"})

    def test_group_allows_duplicates(self):
        self.user.group_ids += self.env.ref("deltatech_product_unique_code.group_product_duplicate_code")
        product = self.Product.create({"name": "Unique B", "default_code": "UQ-A"})
        self.assertEqual(product.default_code, "UQ-A")
