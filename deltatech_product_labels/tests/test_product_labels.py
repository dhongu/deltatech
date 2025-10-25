# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductLabels(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Basic pricelist for price computation
        cls.pricelist = cls.env["product.pricelist"].create({"name": "PL Test"})
        # Base product/template for simple tests
        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Test Product Template",
                "list_price": 12.0,
            }
        )
        cls.product = cls.product_tmpl.product_variant_id
        # Ensure a default_code so barcode fallback works
        cls.product.default_code = "TP-001"
        # Storable, tracked product for stock/lot/quant tests
        cls.stock_tmpl = cls.env["product.template"].create(
            {
                "name": "Stocked Lot Product",
                "list_price": 5.0,
                "tracking": "lot",
                "is_storable": True,
            }
        )
        cls.stock_product = cls.stock_tmpl.product_variant_id
        cls.stock_product.default_code = "SLP-001"
        # Common locations/picking types
        cls.loc_stock = cls.env.ref("stock.stock_location_stock")
        cls.loc_cust = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    def test_get_wrapped_and_action_override(self):
        # Enable override via system parameter
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("terrabit_labels.override_print_button", "True")

        # get_wrapped should wrap by given length and hide default_code in display_name context
        wrapped = self.product.get_wrapped(5)
        self.assertIsInstance(wrapped, list)
        self.assertGreaterEqual(len(wrapped), 1)

        # action_open_label_layout should return our custom action when override is True
        action = self.product.action_open_label_layout()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "product.product.label")

        # Disable override and ensure standard action is still a dict (sanity)
        ICP.set_param("terrabit_labels.override_print_button", "False")
        action2 = self.product.action_open_label_layout()
        self.assertIsInstance(action2, dict)

    def test_wizard_default_get_from_product_and_template(self):
        # From product.product context
        wiz = (
            self.env["product.product.label"]
            .with_context(active_model="product.product", active_ids=[self.product.id])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        self.assertTrue(wiz.label_lines, "Wizard should prefill label lines from product")
        self.assertEqual(wiz.label_lines[0].product_id, self.product)

        # Price compute via onchange_pricelist
        wiz.pricelist_id = self.pricelist.id
        wiz.onchange_pricelist()
        self.assertGreaterEqual(wiz.label_lines[0].price, 0.0)

        # From product.template context
        wiz2 = (
            self.env["product.product.label"]
            .with_context(active_model="product.template", active_ids=[self.product_tmpl.id])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        self.assertTrue(wiz2.label_lines, "Wizard should prefill label lines from template")
        self.assertIn(wiz2.label_lines[0].product_id.id, self.product_tmpl.product_variant_ids.ids)

    def test_print_labels_no_error(self):
        wiz = (
            self.env["product.product.label"]
            .with_context(active_model="product.product", active_ids=[self.product.id])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        # Call print; ensure it returns an action dict
        action = wiz.print_labels()
        self.assertIsInstance(action, dict)

    def test_get_saleorder_lines_and_default_from_so(self):
        # Create sale order with two lines for same product to test aggregation
        so = self.env["sale.order"].create({"partner_id": self.env["res.partner"].create({"name": "SO Cust"}).id})
        self.env["sale.order.line"].create(
            {
                "order_id": so.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "name": self.product.display_name,
                "price_unit": 10.0,
            }
        )
        self.env["sale.order.line"].create(
            {
                "order_id": so.id,
                "product_id": self.product.id,
                "product_uom_qty": 3,
                "name": self.product.display_name,
                "price_unit": 10.0,
            }
        )
        # Call get_saleorder_lines directly
        wiz_model = self.env["product.product.label"]
        lines_dict = wiz_model.get_saleorder_lines([so.id])
        self.assertIn(self.product.id, lines_dict)
        self.assertEqual(lines_dict[self.product.id]["quantity"], 5)
        # Default_get via context should turn dict into label_lines commands
        wiz = wiz_model.with_context(active_model="sale.order", active_ids=[so.id]).create(
            {"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id}
        )
        self.assertTrue(wiz.label_lines)
        self.assertEqual(sum(wiz.label_lines.mapped("quantity")), 5)

    def _make_quant(self, product, location, qty, lot=None):
        Quant = self.env["stock.quant"].with_context(inventory_mode=True)
        if lot:
            return Quant.create(
                {
                    "product_id": product.id,
                    "location_id": location.id,
                    "quantity": qty,
                    "lot_id": lot.id,
                }
            )
        return Quant.create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "quantity": qty,
            }
        )

    def test_get_lot_and_quant_lines(self):
        # Create lot and quant for stock_product
        lot = self.env["stock.lot"].create({"name": "LOT-001", "product_id": self.stock_product.id})
        quant = self._make_quant(self.stock_product, self.loc_stock, 7.0, lot=lot)
        # get_lot_lines
        wiz_model = self.env["product.product.label"]
        lot_lines = wiz_model.get_lot_lines([lot.id])
        self.assertEqual(lot_lines[0][2]["lot"], "LOT-001")
        self.assertGreaterEqual(lot_lines[0][2]["quantity"], 1)
        # get_quant_lines
        quant_lines = wiz_model.get_quant_lines([quant.id])
        self.assertEqual(quant_lines[0][2]["product_id"], self.stock_product.id)
        self.assertEqual(quant_lines[0][2]["lot"], "LOT-001")
        self.assertEqual(quant_lines[0][2]["quantity"], 7.0)

    def test_get_picking_lines_and_generate_lots(self):
        # Create incoming picking with one move line for lot-tracked product without lot_name
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_stock.id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": "M1",
                "product_id": self.stock_product.id,
                "product_uom": self.stock_product.uom_id.id,
                "product_uom_qty": 1.0,
                "picking_id": picking.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_stock.id,
            }
        )
        self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "product_id": self.stock_product.id,
                "product_uom_id": self.stock_product.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_stock.id,
            }
        )
        wiz = (
            self.env["product.product.label"]
            .with_context(active_model="stock.picking", active_ids=[picking.id])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        # get_picking_lines via default should reflect move lines
        self.assertTrue(wiz.label_lines)
        # Now generate lots should assign lot_name and rebuild lines
        wiz.auto_generate_lots = False
        wiz.generate_lots()
        self.assertTrue(picking.move_line_ids[0].lot_name)
        self.assertTrue(wiz.label_lines)

    def test_onchange_lots_option_product_and_template(self):
        # Prepare quants with lots for both product and template contexts
        lot = self.env["stock.lot"].create({"name": "L-ONCH", "product_id": self.stock_product.id})
        self._make_quant(self.stock_product, self.loc_stock, 4.0, lot=lot)
        # Template context
        wiz_t = (
            self.env["product.product.label"]
            .with_context(active_model="product.template", active_ids=[self.stock_tmpl.id])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        wiz_t.print_only_lots = True
        wiz_t.onchange_lots_option()
        self.assertTrue(wiz_t.label_lines)
        self.assertTrue(all(bool(l.lot) for l in wiz_t.label_lines))
        # Product context
        wiz_p = (
            self.env["product.product.label"]
            .with_context(active_model="product.product", active_ids=[self.stock_product.id])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        wiz_p.print_only_lots = True
        wiz_p.onchange_lots_option()
        self.assertTrue(wiz_p.label_lines)
        # quantity is forced to 1 for product context according to implementation
        self.assertTrue(all(l.quantity == 1 for l in wiz_p.label_lines))

    def test_label_line_helpers(self):
        # Create wizard and a line
        wiz = (
            self.env["product.product.label"]
            .with_context(active_model="product.product", active_ids=[self.product.id])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        line = wiz.label_lines[0]
        # get_label_data
        data = line.get_label_data()
        self.assertEqual(data["label_id"], wiz.id)
        self.assertEqual(data["name"], line.product_id.name)
        # get_location_line should safely return False if feature not installed
        self.assertFalse(line.get_location_line())
        # get_barcode_url requires base url param
        self.env["ir.config_parameter"].sudo().set_param("web.base.url", "http://example.test")
        url = line.get_barcode_url(code_format="Code128", barcode="TEST", width=100, height=40)
        self.assertIsInstance(url, str)
        self.assertIn("/report/barcode/", url)
        # compute barcode image works with default_code fallback
        line._compute_barcode_image()
        self.assertTrue(line.barcode_image)
