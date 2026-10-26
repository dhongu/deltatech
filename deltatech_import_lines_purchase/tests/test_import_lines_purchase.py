# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.deltatech_import_lines.tests.common import ImportLinesCommon


@tagged("post_install", "-at_install")
class TestImportLinesPurchase(ImportLinesCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Import Vendor", "is_company": True})
        cls.other_vendor = cls.env["res.partner"].create({"name": "Other Vendor", "is_company": True})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Import Screw",
                "default_code": "IL-S",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.vendor.id, "product_code": "V-100", "price": 7.5}),
                    (0, 0, {"partner_id": cls.other_vendor.id, "product_code": "V-200", "price": 9.0}),
                ],
            }
        )
        cls.order = cls.env["purchase.order"].create({"partner_id": cls.vendor.id})

    def test_import_by_vendor_code(self):
        rows = [["Code", "Qty"], ["V-100", "10"], ["V-200", "1"]]
        wizard = self._open_wizard(self.order, rows, match_by="vendor_code")
        wizard.action_preview()
        self.assertEqual(wizard.row_ids.mapped("status"), ["ok", "not_found"])
        wizard.skip_errors = True
        wizard.action_import()
        self.assertRecordValues(
            self.order.order_line, [{"product_id": self.product.id, "product_qty": 10.0, "price_unit": 7.5}]
        )

    def test_import_price_from_file(self):
        rows = [["Code", "Qty", "Price"], ["IL-S", "3", "6,25"]]
        wizard = self._open_wizard(self.order, rows)
        wizard.action_preview()
        wizard.action_import()
        self.assertRecordValues(self.order.order_line, [{"product_qty": 3.0, "price_unit": 6.25}])

    def test_vendor_code_not_allowed_on_sale_keys(self):
        self.assertIn("vendor_code", self.order._import_lines_match_keys())
        self.order.button_confirm()
        with self.assertRaises(UserError):
            self._open_wizard(self.order, [["Code", "Qty"], ["IL-S", "1"]])
