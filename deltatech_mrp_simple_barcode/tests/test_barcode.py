# ©  2008-2025 Deltatech
# See README.rst file on addons root folder for license details

from lxml import etree

from odoo.tests import Form, TransactionCase, tagged


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

    # Odoo 20: mixinul `barcodes.barcode_events_mixin` a dispărut din core;
    # câmpul `_barcode_scanned` și onchange-ul sunt acum în acest modul.
    def test_onchange_barcode_field_adds_product_and_resets(self):
        mrp = self._new_mrp()
        mrp._barcode_scanned = "BC-A-001"
        res = mrp._on_barcode_scanned()
        self.assertEqual(mrp.product_out_ids.product_id, self.product_a)
        self.assertFalse(mrp._barcode_scanned, "câmpul trebuie golit după scanare")
        self.assertEqual(res["warning"]["type"], "notification")

    def test_onchange_empty_barcode_does_nothing(self):
        mrp = self._new_mrp()
        self.assertIsNone(mrp._on_barcode_scanned())
        self.assertFalse(mrp.product_out_ids)

    def test_form_view_has_barcode_handler_widget(self):
        arch = self.env["mrp.simple"].get_view(view_type="form")["arch"]
        nodes = etree.fromstring(arch).xpath("//field[@name='_barcode_scanned']")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].get("widget"), "deltatech_mrp_simple_barcode_handler")

    def test_form_scan_through_onchange(self):
        # fluxul real din client: widget-ul scrie codul în `_barcode_scanned`,
        # onchange-ul adaugă/incrementează linia și întoarce un warning (notificare)
        form = Form(self.env["mrp.simple"])
        with self.assertLogs("odoo.tests.form.onchange", level="WARNING"):
            form._barcode_scanned = "BC-A-001"
        with self.assertLogs("odoo.tests.form.onchange", level="WARNING"):
            form._barcode_scanned = "BC-A-001"
        lines = form.product_out_ids._records
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["product_id"], self.product_a.id)
        self.assertEqual(lines[0]["quantity"], 2.0)
        self.assertFalse(form._barcode_scanned)
