# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRecordTypeReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Record Type Partner"})
        cls.product = cls.env["product.product"].create({"name": "Record Type Product", "type": "consu"})
        cls.so_type = cls.env["record.type"].create({"name": "SO Type", "model": "sale.order"})
        cls.po_type = cls.env["record.type"].create({"name": "PO Type", "model": "purchase.order"})

    def test_sale_report_so_type(self):
        self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "so_type": self.so_type.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 2, "price_unit": 5})],
            }
        )
        self.env.flush_all()
        lines = self.env["sale.report"].search([("so_type", "=", self.so_type.id)])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.product_uom_qty, 2)
        groups = self.env["sale.report"].formatted_read_group(
            [("so_type", "=", self.so_type.id)], ["so_type"], ["product_uom_qty:sum"]
        )
        self.assertEqual(groups[0]["product_uom_qty:sum"], 2)

    def test_purchase_report_po_type(self):
        self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "po_type": self.po_type.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_qty": 3, "price_unit": 5})],
            }
        )
        self.env.flush_all()
        lines = self.env["purchase.report"].search([("po_type", "=", self.po_type.id)])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.qty_ordered, 3)
        groups = self.env["purchase.report"].formatted_read_group(
            [("po_type", "=", self.po_type.id)], ["po_type"], ["qty_ordered:sum"]
        )
        self.assertEqual(groups[0]["qty_ordered:sum"], 3)
