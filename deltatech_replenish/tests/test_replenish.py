from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductReplenish(TransactionCase):
    """Regression guard: since 19.0 the vendor on the replenishment wizard is
    provided by the standard `purchase_stock` module. These tests make sure the
    behaviour this module used to add is still available out of the box."""

    def setUp(self):
        super().setUp()

        self.warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)

        # Create a product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "purchase_ok": True,
                "list_price": 100.0,
                "standard_price": 50.0,
            }
        )

        # Create a supplier
        self.supplier = self.env["res.partner"].create({"name": "Test Supplier"})

        # Create a supplierinfo
        self.supplierinfo = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.supplier.id,
                "min_qty": 1,
                "price": 50.0,
                "product_tmpl_id": self.product.product_tmpl_id.id,
            }
        )

        self.buy_route = (
            self.env["stock.rule"]
            .search(
                [
                    ("action", "=", "buy"),
                    ("company_id", "=", self.env.company.id),
                    ("picking_type_id.code", "=", "incoming"),
                ],
                limit=1,
            )
            .route_id
        )

        # Create a product replenish wizard
        self.product_replenish = self.env["product.replenish"].create(
            {
                "product_id": self.product.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_uom_id": self.product.uom_id.id,
                "quantity": 7.0,
                "warehouse_id": self.warehouse.id,
                "company_id": self.env.company.id,
                "route_id": self.buy_route.id,
                "supplier_id": self.supplierinfo.id,
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

    def test_vendor_field_is_available(self):
        self.assertTrue(
            self.product_replenish.show_vendor,
            "The vendor field must be displayed when the route buys the product",
        )

    def test_launch_replenishment_uses_selected_vendor(self):
        self.product_replenish.launch_replenishment()
        line = self.env["purchase.order.line"].search([("product_id", "=", self.product.id)], limit=1)
        self.assertTrue(line, "A purchase order line should have been generated")
        self.assertEqual(line.order_id.partner_id, self.supplier)
        self.assertEqual(line.product_qty, 7.0)
