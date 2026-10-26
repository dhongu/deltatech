# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.deltatech_import_lines.tests.common import ImportLinesCommon


@tagged("post_install", "-at_install")
class TestImportLinesSale(ImportLinesCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Import Customer"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Import Chair", "default_code": "IL-A", "barcode": "5940000000011", "list_price": 100.0}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Import Table", "default_code": "IL-B", "list_price": 250.0}
        )
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def test_import_by_reference_with_pricelist_price(self):
        rows = [["Code", "Quantity"], ["IL-A", "2"], ["IL-B", "1,5"]]
        wizard = self._open_wizard(self.order, rows)
        self.assertEqual(wizard.column_ids.mapped("target"), ["product", "quantity"])
        wizard.action_preview()
        self.assertEqual(wizard.ok_count, 2)
        wizard.action_import()
        self.assertRecordValues(
            self.order.order_line,
            [
                {"product_id": self.product_a.id, "product_uom_qty": 2.0, "price_unit": 100.0},
                {"product_id": self.product_b.id, "product_uom_qty": 1.5, "price_unit": 250.0},
            ],
        )
        self.assertTrue(
            self.order.order_line[0].tax_ids
            == self.product_a.taxes_id.filtered(lambda t: t.company_id == self.order.company_id)
        )

    def test_import_price_discount_uom_from_file(self):
        self.env.ref("uom.product_uom_dozen").active = True
        rows = [["Product", "Qty", "Price", "Discount", "UoM"], ["IL-A", "1", "1.234,50", "10", "Dozens"]]
        wizard = self._open_wizard(self.order, rows, file_type="xlsx")
        wizard.action_preview()
        wizard.action_import()
        self.assertRecordValues(
            self.order.order_line,
            [
                {
                    "product_id": self.product_a.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 1234.5,
                    "discount": 10.0,
                    "product_uom_id": self.env.ref("uom.product_uom_dozen").id,
                }
            ],
        )

    def test_match_by_barcode_and_name(self):
        wizard = self._open_wizard(self.order, [["5940000000011", "3"]], has_header=False, match_by="barcode")
        self._set_targets(wizard, {1: "product", 2: "quantity"})
        wizard.action_preview()
        wizard.action_import()
        self.assertEqual(self.order.order_line.product_id, self.product_a)

        rows = [["[IL-B] Import Table", "1"], ["import table", "2"], ["[XX] Import Chair", "1"], ["Missing", "1"]]
        wizard = self._open_wizard(self.order, rows, has_header=False, match_by="name")
        self._set_targets(wizard, {1: "product", 2: "quantity"})
        wizard.action_preview()
        self.assertEqual(wizard.row_ids.mapped("product_id"), self.product_b | self.product_a)
        self.assertEqual(wizard.ok_count, 3)

    def test_unmatched_rows_block_import(self):
        rows = [["Code", "Qty"], ["IL-A", "1"], ["MISSING", "1"], ["IL-B", "abc"], ["IL-B", "1"], ["", "Total"]]
        wizard = self._open_wizard(self.order, rows)
        wizard.action_preview()
        self.assertEqual(len(wizard.row_ids), 4)
        statuses = {row.product_ref + (row.message or ""): row.status for row in wizard.row_ids}
        self.assertEqual(statuses["MISSINGMISSING"], "not_found")
        self.assertEqual(statuses["IL-Babc"], "invalid_quantity")
        with self.assertRaises(UserError):
            wizard.action_import()
        wizard.skip_errors = True
        wizard.action_import()
        self.assertEqual(self.order.order_line.product_id, self.product_a | self.product_b)

    def test_invalid_uom(self):
        rows = [["Code", "Qty", "UoM"], ["IL-A", "1", "kg"]]
        wizard = self._open_wizard(self.order, rows)
        wizard.action_preview()
        self.assertEqual(wizard.row_ids.status, "invalid_uom")

    def test_mapping_saved_per_partner(self):
        rows = [["Art.", "Buc"], ["IL-A", "4"]]
        wizard = self._open_wizard(self.order, rows)
        self.assertFalse(any(wizard.column_ids.mapped("target")))
        self._set_targets(wizard, {1: "product", 2: "quantity"})
        wizard.write({"mapping_name": "Customer file", "mapping_for_partner": True})
        wizard.action_save_mapping()
        mapping = wizard.mapping_id
        self.assertEqual(mapping.partner_id, self.partner)
        self.assertEqual(mapping.res_model, "sale.order")

        other_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        wizard = self._open_wizard(other_order, [["Buc", "Art."], ["2", "IL-B"]])
        self.assertEqual(wizard.mapping_id, mapping)
        self.assertEqual(wizard.column_ids.mapped("target"), ["quantity", "product"])
        wizard.action_preview()
        wizard.action_import()
        self.assertEqual(other_order.order_line.product_uom_qty, 2.0)

        generic_order = self.env["sale.order"].create({"partner_id": self.env["res.partner"].create({"name": "X"}).id})
        wizard = self._open_wizard(generic_order, rows)
        self.assertFalse(wizard.mapping_id)

    def test_confirmed_order_refused(self):
        self.order.order_line = [(0, 0, {"product_id": self.product_a.id})]
        self.order.action_confirm()
        with self.assertRaises(UserError):
            self._open_wizard(self.order, [["Code", "Qty"], ["IL-A", "1"]])

    def test_document_model_checked(self):
        wizard = self._open_wizard(self.order, [["Code", "Qty"], ["IL-A", "1"]])
        wizard.res_model = "res.partner"
        with self.assertRaises(UserError):
            wizard.action_preview()

    def test_target_not_used_by_document(self):
        wizard = self._open_wizard(self.order, [["Code", "Qty", "Lot"], ["IL-A", "1", "L1"]])
        with self.assertRaises(UserError):
            wizard.action_preview()
