# © 2025 Deltatech
# See README.rst file on addons root folder for license details


from .test_common import TestCommon


class TestStockMoveAccountDetermination(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create product category with real-time valuation
        cls.product_category = cls.env["product.category"].create(
            {
                "name": "Test Category",
                "property_valuation": "real_time",
                "property_cost_method": "standard",
            }
        )

        # Create test product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "categ_id": cls.product_category.id,
                "valuation_class_id": cls.valuation_class.id,
                "standard_price": 100.0,
            }
        )

        # Create stock locations
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")

        # Create picking types
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.picking_type_internal = cls.env.ref("stock.picking_type_internal")

        # Create account determination rules
        cls.env["product.account.determination"].create(
            {
                "transaction_key": "stock_receipt",
                "valuation_class_id": cls.valuation_class.id,
                "valuation_area_id": cls.valuation_area.id,
                "company_id": cls.env.company.id,
                "acc_src_id": cls.account_src.id,
                "acc_dest_id": cls.account_dest.id,
                "acc_valuation_id": cls.account_valuation.id,
            }
        )

        cls.env["product.account.determination"].create(
            {
                "transaction_key": "stock_delivery",
                "valuation_class_id": cls.valuation_class.id,
                "valuation_area_id": cls.valuation_area.id,
                "company_id": cls.env.company.id,
                "acc_src_id": cls.account_dest.id,
                "acc_dest_id": cls.account_src.id,
                "acc_valuation_id": cls.account_valuation.id,
            }
        )

        cls.env["product.account.determination"].create(
            {
                "transaction_key": "internal_transfer",
                "valuation_class_id": cls.valuation_class.id,
                "valuation_area_id": cls.valuation_area.id,
                "company_id": cls.env.company.id,
                "acc_src_id": cls.account_src.id,
                "acc_dest_id": cls.account_dest.id,
                "acc_valuation_id": cls.account_valuation.id,
            }
        )

    def test_01_compute_transaction_key_receipt(self):
        """Test computing transaction key for receipt"""
        # Create a receipt picking
        picking_in = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Add move line
        move_in = self.env["stock.move"].create(
            {
                "name": "Test Receipt",
                "picking_id": picking_in.id,
                "product_id": self.product.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Check that transaction key is computed correctly
        self.assertEqual(move_in._compute_transaction_key(), "stock_receipt")

    def test_02_compute_transaction_key_delivery(self):
        """Test computing transaction key for delivery"""
        # Create some initial stock
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 10.0)

        # Create a delivery picking
        picking_out = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        # Add move line
        move_out = self.env["stock.move"].create(
            {
                "name": "Test Delivery",
                "picking_id": picking_out.id,
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        # Check that transaction key is computed correctly
        self.assertEqual(move_out._compute_transaction_key(), "stock_delivery")

    def test_03_compute_transaction_key_internal(self):
        """Test computing transaction key for internal transfer"""
        # Create an internal location
        internal_location = self.env["stock.location"].create(
            {
                "name": "Test Internal Location",
                "usage": "internal",
                "location_id": self.stock_location.id,
            }
        )

        # Create some initial stock
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 10.0)

        # Create an internal transfer
        picking_internal = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_internal.id,
                "location_id": self.stock_location.id,
                "location_dest_id": internal_location.id,
            }
        )

        # Add move line
        move_internal = self.env["stock.move"].create(
            {
                "name": "Test Internal Transfer",
                "picking_id": picking_internal.id,
                "product_id": self.product.id,
                "product_uom_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": internal_location.id,
            }
        )

        # Check that transaction key is computed correctly
        self.assertEqual(move_internal._compute_transaction_key(), "internal_transfer")

    def test_04_get_account_determination(self):
        """Test getting account determination from stock move"""
        # Create a receipt picking
        picking_in = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Add move line
        move_in = self.env["stock.move"].create(
            {
                "name": "Test Receipt",
                "picking_id": picking_in.id,
                "product_id": self.product.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )

        # Get account determination rule
        journal_id, acc_src, acc_dest, acc_valuation = move_in._get_accounting_data_for_valuation()

        # Check accounts
        self.assertEqual(acc_src, self.account_src.id)
        self.assertEqual(acc_dest, self.account_dest.id)
        self.assertEqual(acc_valuation, self.account_valuation.id)

    def test_05_account_entry_move_with_valid_data(self):
        """Test _account_entry_move with valid data."""
        stock_move = self.env["stock.move"].create(
            {
                "name": "Test move",
                "product_id": self.product.id,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "product_uom_qty": 10,
                "state": "done",
            }
        )
        qty = 10
        description = "Test Description"
        svl_id = self.env["stock.valuation.layer"].create(
            {
                "stock_move_id": stock_move.id,
                "value": 100.0,
                "unit_cost": 10.0,
                "company_id": self.env.company.id,
                "product_id": self.product.id,
            }
        )
        cost = 100.0
        stock_move._account_entry_move(qty, description, svl_id.id, cost)
