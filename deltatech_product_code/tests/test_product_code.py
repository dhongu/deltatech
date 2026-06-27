# ©  2023Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductCode(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        # pregatire categorie noua pentru test in care se sa fie definita secventa de coduri

        # creare secventa de coduri
        sequence = self.env["ir.sequence"].create(
            {
                "name": "Product Code",
                "code": "product.code",
                "prefix": "TEST/",
                "padding": 4,
                "number_increment": 1,
                "implementation": "standard",
            }
        )
        # creare categorie noua
        self.product_category = self.env["product.category"].create(
            {
                "name": "Test",
                "sequence_id": sequence.id,
                "generate_barcode": True,
            }
        )

    def test_new_product_template(self):
        # creare produs nou
        product_template = self.env["product.template"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
            }
        )
        # verificare daca a fost generat codul
        self.assertEqual(product_template.default_code, "TEST/0001")

    def test_new_product_product(self):
        # creare produs nou
        product_product = self.env["product.product"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
            }
        )
        # verificare daca a fost generat codul
        self.assertEqual(product_product.default_code, "TEST/0001")

    def test_now_product_with_barcode(self):
        self.product_category.write({"generate_barcode": True, "barcode_random": False})
        product_template = self.env["product.template"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
            }
        )
        self.assertTrue(product_template.barcode)
        self.assertTrue(product_template.barcode.startswith(self.product_category.prefix_barcode))

    def test_button_new_code(self):
        product_template = self.env["product.template"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
                "default_code": "MANUAL001",
            }
        )
        self.assertEqual(product_template.default_code, "MANUAL001")
        product_template.button_new_code()
        # button_new_code only updates if code is in [False, "/", "auto"]
        self.assertEqual(product_template.default_code, "MANUAL001")

        product_template.default_code = "/"
        product_template.button_new_code()
        self.assertTrue(product_template.default_code.startswith("TEST/"))

        # Test button_new_code on product.product
        product_product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "categ_id": self.product_category.id,
                "default_code": "PMANUAL001",
            }
        )
        self.assertEqual(product_product.default_code, "PMANUAL001")
        product_product.button_new_code()
        self.assertEqual(product_product.default_code, "PMANUAL001")

        product_product.default_code = "/"
        product_product.button_new_code()
        self.assertTrue(product_product.default_code.startswith("TEST/"))

    def test_button_new_code_variants(self):
        # Verify product.template.button_new_code updates variant codes
        attribute = self.env["product.attribute"].create({"name": "Color", "create_variant": "always"})
        val1 = self.env["product.attribute.value"].create({"name": "Red", "attribute_id": attribute.id})

        product_template = self.env["product.template"].create(
            {
                "name": "Template with Variant",
                "categ_id": self.product_category.id,
                "default_code": "TMANUAL",
                "attribute_line_ids": [(0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, [val1.id])]})],
            }
        )
        variant = product_template.product_variant_ids[0]
        # Initially they might have codes or not depending on creation logic
        # Let's force them to "/"
        product_template.default_code = "/"
        variant.default_code = "/"

        product_template.button_new_code()

        self.assertTrue(product_template.default_code.startswith("TEST/"))
        self.assertEqual(variant.default_code, product_template.default_code)

    def test_force_new_code(self):
        product_template = self.env["product.template"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
                "default_code": "MANUAL001",
            }
        )
        product_template.force_new_code()
        self.assertTrue(product_template.default_code.startswith("TEST/"))

    def test_product_variant_code(self):
        # Test variant creation and code generation
        attribute = self.env["product.attribute"].create({"name": "Size", "create_variant": "always"})
        val1 = self.env["product.attribute.value"].create({"name": "S", "attribute_id": attribute.id})
        val2 = self.env["product.attribute.value"].create({"name": "M", "attribute_id": attribute.id})

        product_template = self.env["product.template"].create(
            {
                "name": "Configurable Product",
                "categ_id": self.product_category.id,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, [val1.id, val2.id])]})
                ],
            }
        )
        # In this case, template should NOT get a code if it has variants (commented out in code but good to check current behavior)
        # Based on product.py lines 60-91 (commented out) and 118-149
        for variant in product_template.product_variant_ids:
            self.assertTrue(variant.default_code.startswith("TEST/"))

    def test_duplicate_code_blocked_template(self):
        # produsele de test au company_id = False (NULL) — cazul pe care
        # vechea constrangere SQL unique(default_code, active, company_id) il rata
        self.env["product.template"].create(
            {"name": "Prod A", "categ_id": self.product_category.id, "default_code": "DUP001"}
        )
        with self.assertRaises(ValidationError):
            self.env["product.template"].create(
                {"name": "Prod B", "categ_id": self.product_category.id, "default_code": "DUP001"}
            )

    def test_duplicate_code_blocked_product(self):
        self.env["product.product"].create(
            {"name": "Var A", "categ_id": self.product_category.id, "default_code": "DUP002"}
        )
        with self.assertRaises(ValidationError):
            self.env["product.product"].create(
                {"name": "Var B", "categ_id": self.product_category.id, "default_code": "DUP002"}
            )

    def test_duplicate_code_blocked_in_same_batch(self):
        # doua coduri identice in acelasi create in lot trebuie blocate
        with self.assertRaises(ValidationError):
            self.env["product.template"].create(
                [
                    {"name": "Prod A", "categ_id": self.product_category.id, "default_code": "DUP010"},
                    {"name": "Prod B", "categ_id": self.product_category.id, "default_code": "DUP010"},
                ]
            )

    def test_duplicate_code_archived_allowed(self):
        # un produs arhivat nu trebuie sa blocheze refolosirea codului
        product_a = self.env["product.template"].create(
            {"name": "Prod A", "categ_id": self.product_category.id, "default_code": "DUP003"}
        )
        product_a.active = False
        product_b = self.env["product.template"].create(
            {"name": "Prod B", "categ_id": self.product_category.id, "default_code": "DUP003"}
        )
        self.assertEqual(product_b.default_code, "DUP003")

    def test_barcode_random(self):
        self.product_category.write({"generate_barcode": True, "barcode_random": True})
        product_template = self.env["product.template"].create(
            {
                "name": "Test Random Barcode",
                "categ_id": self.product_category.id,
            }
        )
        self.assertTrue(product_template.barcode)
        self.assertEqual(len(product_template.barcode), 13)  # EAN13
