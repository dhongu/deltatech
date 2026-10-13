# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductUniqueCode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bypass_group = cls.env.ref("deltatech_product_unique_code.group_product_duplicate_code")
        cls.user = cls.env["res.users"].create(
            {
                "name": "Unique Code Tester",
                "login": "unique_code_tester",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        # root/admin are members of the bypass group: run the checks as a regular user (with sudo rights)
        cls.uenv = cls.env(user=cls.user, su=True)
        cls.Product = cls.uenv["product.product"]
        cls.Template = cls.uenv["product.template"]
        cls.product_a = cls.Product.create({"name": "UC Product A", "default_code": "UC-A", "barcode": "UC-BAR-A"})

    def test_user_not_in_bypass_group(self):
        self.assertFalse(self.uenv.user.has_group("deltatech_product_unique_code.group_product_duplicate_code"))

    def test_field_labels(self):
        self.assertEqual(self.Product._unique_code_field_label("default_code"), "Internal Reference")
        self.assertEqual(self.Product._unique_code_field_label("barcode"), "Barcode")

    def test_create_unique_product_ok(self):
        product = self.Product.create({"name": "UC Product B", "default_code": "UC-B", "barcode": "UC-BAR-B"})
        self.assertEqual(product.default_code, "UC-B")

    def test_create_without_codes_ok(self):
        product = self.Product.create({"name": "UC No code"})
        self.assertFalse(product.default_code)
        # empty values are skipped (early return)
        self.Product._check_unique_code_all(product)

    def test_create_product_duplicate_default_code(self):
        with self.assertRaises(ValidationError) as err:
            self.Product.create({"name": "UC Dup", "default_code": "UC-A"})
        self.assertIn("Internal Reference", str(err.exception))
        self.assertIn("UC-A", str(err.exception))
        self.assertIn("including archived", str(err.exception))

    def test_create_template_duplicate_default_code(self):
        with self.assertRaises(ValidationError):
            self.Template.create({"name": "UC Dup Tmpl", "default_code": "UC-A"})

    def test_create_duplicate_of_archived_product(self):
        archived = self.Product.create({"name": "UC Archived", "default_code": "UC-ARCH", "barcode": "UC-BAR-ARCH"})
        archived.action_archive()
        self.assertFalse(archived.active)
        with self.assertRaises(ValidationError) as err:
            self.Product.create({"name": "UC New", "default_code": "UC-ARCH"})
        self.assertIn("UC Archived", str(err.exception))
        # the core barcode constraint ignores archived products, this module does not
        with self.assertRaises(ValidationError) as err:
            self.Product.create({"name": "UC New 2", "barcode": "UC-BAR-ARCH"})
        self.assertIn("Barcode", str(err.exception))
        self.assertIn("including archived", str(err.exception))

    def test_archive_duplicate_allowed(self):
        self.product_a.action_archive()
        self.assertFalse(self.product_a.active)
        self.product_a.action_unarchive()
        self.assertTrue(self.product_a.active)

    def test_write_product_duplicate(self):
        product = self.Product.create({"name": "UC Product C", "default_code": "UC-C"})
        with self.assertRaises(ValidationError):
            product.write({"default_code": "UC-A"})

    def test_write_product_unique_and_other_fields(self):
        product = self.Product.create({"name": "UC Product D", "default_code": "UC-D"})
        product.write({"name": "UC Product D renamed"})
        product.write({"default_code": "UC-D2", "barcode": "UC-BAR-D2"})
        self.assertEqual(product.default_code, "UC-D2")
        # clearing the code is always allowed
        product.write({"default_code": False})
        self.assertFalse(product.default_code)

    def test_write_template_duplicate(self):
        template = self.Template.create({"name": "UC Tmpl E", "default_code": "UC-E"})
        with self.assertRaises(ValidationError):
            template.write({"default_code": "UC-A"})

    def test_write_template_ok(self):
        template = self.Template.create({"name": "UC Tmpl F", "default_code": "UC-F"})
        template.write({"name": "UC Tmpl F renamed"})
        template.write({"default_code": "UC-F2", "barcode": "UC-BAR-F2"})
        self.assertEqual(template.product_variant_id.default_code, "UC-F2")
        self.assertEqual(template.product_variant_id.barcode, "UC-BAR-F2")

    def test_existing_duplicates_can_be_cleaned_up(self):
        # create a historical duplicate as a user allowed to do it
        self.bypass_group.write({"user_ids": [(4, self.user.id)]})
        dup = self.Product.create({"name": "UC Historical Dup", "default_code": "UC-A"})
        dup_tmpl = self.Template.create({"name": "UC Historical Tmpl Dup", "default_code": "UC-A"})
        self.bypass_group.write({"user_ids": [(3, self.user.id)]})
        self.env.invalidate_all()
        self.assertFalse(self.uenv.user.has_group("deltatech_product_unique_code.group_product_duplicate_code"))
        # rewriting the same value does not trigger the check
        dup.write({"default_code": "UC-A"})
        dup_tmpl.write({"default_code": "UC-A"})
        # changing another code field is validated only for that field
        dup.write({"barcode": "UC-BAR-HIST"})
        dup_tmpl.write({"barcode": "UC-BAR-HIST-T"})
        # archiving the duplicate is allowed
        dup.action_archive()
        # renaming to a fresh code is allowed
        dup.write({"default_code": "UC-A-OLD"})
        dup_tmpl.write({"default_code": "UC-A-OLD-T"})
        self.assertEqual(dup.default_code, "UC-A-OLD")

    def test_bypass_group(self):
        self.bypass_group.write({"user_ids": [(4, self.user.id)]})
        self.env.invalidate_all()
        product = self.Product.create({"name": "UC Allowed Dup", "default_code": "UC-A"})
        self.assertEqual(product.default_code, "UC-A")
        product.write({"default_code": "UC-A"})
        template = self.Template.create({"name": "UC Allowed Tmpl", "default_code": "UC-A"})
        template.write({"default_code": "UC-A"})

    def test_admin_in_bypass_group(self):
        product = self.env["product.product"].create({"name": "UC Root Dup", "default_code": "UC-A"})
        self.assertEqual(product.default_code, "UC-A")

    def test_template_branch_detection(self):
        # a template duplicate on an archived template whose variants are archived too
        tmpl = self.Template.create({"name": "UC Tmpl Arch", "default_code": "UC-TA"})
        tmpl.action_archive()
        with self.assertRaises(ValidationError) as err:
            self.Template.create({"name": "UC Tmpl New", "default_code": "UC-TA"})
        self.assertIn("UC Tmpl Arch", str(err.exception))
