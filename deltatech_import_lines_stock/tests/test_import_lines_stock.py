# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.deltatech_import_lines.tests.common import ImportLinesCommon


@tagged("post_install", "-at_install")
class TestImportLinesStock(ImportLinesCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.product = cls.env["product.product"].create(
            {"name": "Import Box", "default_code": "IL-BOX", "is_storable": True}
        )
        cls.product_lot = cls.env["product.product"].create(
            {"name": "Import Paint", "default_code": "IL-LOT", "is_storable": True, "tracking": "lot"}
        )
        cls.product_serial = cls.env["product.product"].create(
            {"name": "Import Drill", "default_code": "IL-SN", "is_storable": True, "tracking": "serial"}
        )
        cls.lot = cls.env["stock.lot"].create({"name": "LOT-EXIST", "product_id": cls.product_lot.id})

    def _picking(self, picking_type):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id
                or self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": picking_type.default_location_dest_id.id
                or self.env.ref("stock.stock_location_customers").id,
            }
        )

    def test_receipt_with_new_and_existing_lots(self):
        receipt = self._picking(self.warehouse.in_type_id)
        rows = [
            ["Code", "Qty", "Lot"],
            ["IL-BOX", "5", ""],
            ["IL-LOT", "3", "LOT-NEW"],
            ["IL-LOT", "2", "LOT-EXIST"],
            ["IL-SN", "2", "SN-1"],
            ["IL-BOX", "1", "X"],
        ]
        wizard = self._open_wizard(receipt, rows)
        wizard.action_preview()
        self.assertEqual(wizard.row_ids.mapped("status"), ["ok", "ok", "ok", "lot_error", "lot_error"])
        wizard.skip_errors = True
        wizard.action_import()
        # the two rows of the lot product are merged into one move with a line per lot
        self.assertEqual(len(receipt.move_ids), 2)
        lot_moves = receipt.move_ids.filtered(lambda m: m.product_id == self.product_lot)
        self.assertEqual(
            sorted(lot_moves.move_line_ids.mapped(lambda ml: ml.lot_id.name or ml.lot_name)), ["LOT-EXIST", "LOT-NEW"]
        )
        self.assertEqual(sum(lot_moves.mapped("quantity")), 5.0)

    def test_confirmed_delivery_gets_confirmed_moves(self):
        delivery = self._picking(self.warehouse.out_type_id)
        delivery.move_ids = [
            (
                0,
                0,
                {
                    "product_id": self.product.id,
                    "product_uom_qty": 1.0,
                    "location_id": delivery.location_id.id,
                    "location_dest_id": delivery.location_dest_id.id,
                },
            )
        ]
        delivery.action_confirm()
        wizard = self._open_wizard(delivery, [["Code", "Qty"], ["IL-BOX", "4"]])
        wizard.action_preview()
        wizard.action_import()
        # the confirmation merges the new move into the existing one of the same product
        self.assertEqual(sum(delivery.move_ids.mapped("product_uom_qty")), 5.0)
        self.assertNotIn("draft", delivery.move_ids.mapped("state"))

    def test_lot_not_created_on_delivery(self):
        delivery = self._picking(self.warehouse.out_type_id)
        wizard = self._open_wizard(delivery, [["Code", "Qty", "Lot"], ["IL-LOT", "1", "LOT-UNKNOWN"]])
        wizard.action_preview()
        self.assertEqual(wizard.row_ids.status, "lot_error")

    def test_inventory_count(self):
        quant_model = self.env["stock.quant"]
        rows = [
            ["Code", "Counted", "Lot"],
            ["IL-BOX", "7", ""],
            ["IL-BOX", "3", ""],
            ["IL-LOT", "0", "LOT-EXIST"],
            ["IL-LOT", "1", "LOT-MISSING"],
        ]
        context = {"import_lines_model": "stock.quant", "inventory_mode": True}
        wizard = self._open_wizard(quant_model, rows, context=context)
        self.assertEqual(wizard.location_id, self.stock_location)
        self._set_targets(wizard, {1: "product", 2: "quantity", 3: "lot"})
        wizard.action_preview()
        self.assertEqual(wizard.row_ids.mapped("status"), ["ok", "ok", "ok", "lot_error"])
        wizard.skip_errors = True
        wizard.action_import()
        quants = quant_model.search(
            [("location_id", "=", self.stock_location.id), ("product_id", "in", (self.product | self.product_lot).ids)]
        )
        box_quant = quants.filtered(lambda q: q.product_id == self.product)
        self.assertEqual(box_quant.inventory_quantity, 10.0)
        self.assertTrue(box_quant.inventory_quantity_set)
        lot_quant = quants.filtered(lambda q: q.lot_id == self.lot)
        self.assertTrue(lot_quant.inventory_quantity_set)
        self.assertEqual(lot_quant.inventory_quantity, 0.0)
