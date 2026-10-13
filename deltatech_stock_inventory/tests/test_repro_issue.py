from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "deltatech_stock_inventory")
class TestQuantCreateRepro(TransactionCase):
    def test_quant_create_with_inventory_mode(self):
        product = self.env["product.product"].create(
            {
                "name": "Test Product Repro",
                "is_storable": True,
            }
        )
        location = self.env.ref("stock.stock_location_stock")

        # Simulăm un utilizator fără grupul special deltatech
        test_user = self.env["res.users"].create(
            {
                "name": "Test User No Group",
                "login": "test_user_no_group",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )

        # Încercăm să creăm quant cu inventory_mode=True
        try:
            self.env["stock.quant"].with_user(test_user).with_context(inventory_mode=True).create(
                {
                    "product_id": product.id,
                    "location_id": location.id,
                    "inventory_quantity": 10,
                }
            )
            print("SUCCESS: Quant created with inventory_mode=True")
        except UserError as e:
            print(f"FAILURE: {e}")
            raise e
