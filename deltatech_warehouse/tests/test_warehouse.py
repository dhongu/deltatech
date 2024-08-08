from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a test product template
        self.product_template = self.env["product.template"].create({"name": "Test Product Template", "scrap": 0.1})

    def test_scrap_factor(self):
        self.assertEqual(self.product_template.scrap, 0.1, "Scrap factor should be 0.1")


class TestResCompany(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a test company with a default supplier
        self.supplier = self.env["res.partner"].create({"name": "Test Supplier"})
        self.company = self.env.user.company_id
        self.company.supplier_id = self.supplier

        # Create a test product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "product_tmpl_id": self.env["product.template"].create({"name": "Test Template"}).id,
                "purchase_ok": True,
            }
        )

    def test_set_supplier(self):
        self.company.set_supplier()
        supplierinfo = self.env["product.supplierinfo"].search([("partner_id", "=", self.supplier.id)])
        self.assertTrue(supplierinfo, "Supplierinfo should be set for products when setting a default supplier")


class TestWarehouse(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a test warehouse
        self.warehouse = self.env["stock.warehouse"].create({"name": "Test Warehouse", "code": "TW"})

        # Create test picking types
        self.picking_type_prod_consume = self.env["stock.picking.type"].create(
            {"name": "Production Consume", "code": "internal", "sequence_code": "PC", "warehouse_id": self.warehouse.id}
        )
        self.picking_type_prod_receipt = self.env["stock.picking.type"].create(
            {"name": "Production Receipt", "code": "internal", "sequence_code": "PR", "warehouse_id": self.warehouse.id}
        )

        # Assign picking types to the warehouse
        self.warehouse.pick_type_prod_consume_id = self.picking_type_prod_consume.id
        self.warehouse.pick_type_prod_receipt_id = self.picking_type_prod_receipt.id

    def test_warehouse_picking_types(self):
        self.assertEqual(
            self.warehouse.pick_type_prod_consume_id,
            self.picking_type_prod_consume,
            "Production consume picking type should be set correctly",
        )
        self.assertEqual(
            self.warehouse.pick_type_prod_receipt_id,
            self.picking_type_prod_receipt,
            "Production receipt picking type should be set correctly",
        )
