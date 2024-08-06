from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductCategory(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a product category
        self.product_category = self.env["product.category"].create(
            {
                "name": "Test Category",
            }
        )
        self.unrestricted_user = self.env["res.users"].create(
            {
                "name": "Restricted User",
                "login": "restricted_user",
                "password": "password",
                "groups_id": [(6, 0, [self.env.ref("deltatech_restricted_access.group_edit_sensible_data").id])],
            }
        )

    def test_write(self):
        # Try to write a disallowed field
        with self.assertRaises(UserError):
            self.product_category.write({"property_valuation": "real_time"})

    def test_write2(self):
        # Try to write a disallowed field
        self.env.user = self.unrestricted_user
        self.product_category.write({"property_valuation": "real_time"})


class TestStockLocation(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a stock location
        self.stock_location = self.env["stock.location"].create(
            {
                "name": "Test Location",
                "location_id": self.env.ref("stock.stock_location_stock").id,
            }
        )
        self.unrestricted_user = self.env["res.users"].create(
            {
                "name": "Restricted User",
                "login": "restricted_user",
                "password": "password",
                "groups_id": [(6, 0, [self.env.ref("deltatech_restricted_access.group_edit_sensible_data").id])],
            }
        )

    def test_write(self):
        # Try to write a disallowed field
        with self.assertRaises(UserError):
            self.stock_location.write({"name": "New Location"})

    def test_write2(self):
        # Try to write a disallowed field
        self.env.user = self.unrestricted_user
        self.stock_location.write({"name": "New Location"})


class TestUoM(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a unit of measure
        self.uom = self.env["uom.uom"].create(
            {
                "name": "Test UoM",
                "category_id": self.env.ref("uom.product_uom_categ_unit").id,
                "uom_type": "bigger",
                "rounding": 0.01,
            }
        )
        self.unrestricted_user = self.env["res.users"].create(
            {
                "name": "Restricted User",
                "login": "restricted_user",
                "password": "password",
                "groups_id": [(6, 0, [self.env.ref("deltatech_restricted_access.group_edit_sensible_data").id])],
            }
        )

    def test_write(self):
        # Try to write a disallowed field
        with self.assertRaises(UserError):
            self.uom.write({"name": "New UoM"})

    def test_write2(self):
        # Try to write a disallowed field
        self.env.user = self.unrestricted_user
        self.uom.write({"name": "New UoM"})
