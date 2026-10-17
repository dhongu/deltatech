# ©  2008-2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMrpSimpleBarcode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env["product.product"]
        cls.product_a = Product.create(
            {
                "name": "Product A",
                "type": "consu",
                "barcode": "BC-A-001",
                "default_code": "REF-A",
            }
        )
        cls.product_b = Product.create(
            {
                "name": "Product B",
                "type": "consu",
                "barcode": "BC-B-002",
            }
        )

    def _new_mrp(self, **vals):
        # Folosim un record `.new()` pentru a reproduce contextul onchange
        # în care `on_barcode_scanned` / `_add_product` rulează în realitate
        # (metoda se bazează pe `self.product_out_ids.new(...)` în memorie).
        return self.env["mrp.simple"].new(vals)

    def test_scan_adds_product_by_barcode(self):
        mrp = self._new_mrp()
        res = mrp.on_barcode_scanned("BC-A-001")
        self.assertEqual(len(mrp.product_out_ids), 1)
        self.assertEqual(mrp.product_out_ids.product_id, self.product_a)
        self.assertEqual(mrp.product_out_ids.quantity, 1.0)
        self.assertEqual(res["warning"]["type"], "notification")

    def test_scan_finds_product_by_internal_reference(self):
        mrp = self._new_mrp()
        mrp.on_barcode_scanned("REF-A")
        self.assertEqual(len(mrp.product_out_ids), 1)
        self.assertEqual(mrp.product_out_ids.product_id, self.product_a)

    def test_scan_same_product_increments_quantity(self):
        mrp = self._new_mrp()
        mrp.on_barcode_scanned("BC-A-001")
        mrp.on_barcode_scanned("BC-A-001")
        self.assertEqual(len(mrp.product_out_ids), 1, "nu trebuie să dubleze linia")
        self.assertEqual(mrp.product_out_ids.quantity, 2.0)

    def test_scan_two_products_creates_two_lines(self):
        mrp = self._new_mrp()
        mrp.on_barcode_scanned("BC-A-001")
        mrp.on_barcode_scanned("BC-B-002")
        self.assertEqual(len(mrp.product_out_ids), 2)
        self.assertEqual(
            mrp.product_out_ids.product_id,
            self.product_a + self.product_b,
        )

    def test_scan_unknown_barcode_returns_warning(self):
        mrp = self._new_mrp()
        res = mrp.on_barcode_scanned("DOES-NOT-EXIST")
        self.assertEqual(res["warning"]["type"], "danger")
        self.assertFalse(mrp.product_out_ids, "nu trebuie să adauge nicio linie")

    def test_scan_blocked_when_not_draft(self):
        mrp = self._new_mrp(state="done")
        res = mrp.on_barcode_scanned("BC-A-001")
        self.assertEqual(res["warning"]["type"], "danger")
        self.assertFalse(mrp.product_out_ids, "starea ≠ draft trebuie să blocheze scanarea")

    def test_scan_ambiguous_internal_reference_returns_warning(self):
        # Issue #3401: referința internă nu e unică; o scanare care găsește
        # mai multe produse nu trebuie să ajungă la acces singleton.
        Product = self.env["product.product"]
        Product.create({"name": "Dup 1", "type": "consu", "default_code": "REF-DUP"})
        Product.create({"name": "Dup 2", "type": "consu", "default_code": "REF-DUP"})
        mrp = self._new_mrp()
        res = mrp.on_barcode_scanned("REF-DUP")
        self.assertEqual(res["warning"]["type"], "danger")
        self.assertIn("Dup 1", res["warning"]["message"])
        self.assertFalse(mrp.product_out_ids, "nu trebuie să adauge nicio linie")
