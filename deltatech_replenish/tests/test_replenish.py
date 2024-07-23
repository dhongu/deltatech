from odoo.tests.common import TransactionCase


class TestProductReplenish(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a new UoM category for testing
        self.uom_category = self.env["uom.category"].create(
            {
                "name": "Test Category",
            }
        )

        # Create a unit of measure in the new category
        self.uom = self.env["uom.uom"].create(
            {
                "name": "Unit",
                "category_id": self.uom_category.id,
                "factor": 1.0,
                "uom_type": "reference",
            }
        )

        # Create a product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "list_price": 100.0,
                "standard_price": 50.0,
                "uom_id": self.uom.id,  # Use the created UOM
                "uom_po_id": self.uom.id,  # Use the created UOM
            }
        )

        # Create a supplier
        self.supplier = self.env["res.partner"].create(
            {
                "name": "Test Supplier",
            }
        )

        # Create a supplierinfo
        self.supplierinfo = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.supplier.id,
                "min_qty": 1,
                "price": 50.0,
                "product_tmpl_id": self.product.product_tmpl_id.id,
            }
        )

        # Create a product replenish wizard
        self.product_replenish = self.env["product.replenish"].create(
            {
                "product_id": self.product.id,
                "supplier_id": self.supplierinfo.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_uom_id": self.uom.id,  # Use the created UOM
            }
        )

    def test_prepare_run_values(self):
        # Prepare run values
        run_values = self.product_replenish._prepare_run_values()
        self.assertEqual(
            run_values["supplierinfo_id"],
            self.supplierinfo,
            "The 'supplierinfo_id' field should be equal to the supplierinfo created in the setup",
        )
