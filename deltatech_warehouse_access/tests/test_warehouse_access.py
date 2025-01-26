# from odoo.exceptions import AccessError
# from odoo.tests.common import TransactionCase
#
#
# class TestStockPickingAccessControl(TransactionCase):
#     def setUp(self):
#         super().setUp()
#
#         self.user_access = self.env["res.users"].create(
#             {"name": "Access User", "login": "access_user", "groups_id": [(6, 0, [self.env.ref("base.group_user").id])]}
#         )
#
#         # Create a warehouse and assign the warehouse manager user
#         self.warehouse = self.env["stock.warehouse"].create(
#             {"name": "Test Warehouse", "code": "TEST", "user_ids": [(6, 0, [self.user_access.id])]}
#         )
#
#         # Create a picking type for the warehouse
#         self.picking_type = self.env["stock.picking.type"].create(
#             {
#                 "name": "Test Picking Type",
#                 "code": "outgoing",
#                 "warehouse_id": self.warehouse.id,
#                 "sequence_code": "TEST_OUT",
#             }
#         )
#
#         # Create a stock picking for the test
#         self.stock_picking = self.env["stock.picking"].create(
#             {
#                 "partner_id": self.env.ref("base.res_partner_12").id,
#                 "location_id": self.env.ref("stock.stock_location_stock").id,
#                 "location_dest_id": self.env.ref("stock.stock_location_customers").id,
#                 "picking_type_id": self.picking_type.id,
#             }
#         )
#
#     def test_user_without_access(self):
#         with self.assertRaises(AccessError):
#             self.stock_picking.button_validate()
