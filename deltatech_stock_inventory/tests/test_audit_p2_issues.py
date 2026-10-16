# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from lxml import etree

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestAuditP2Issues(TransactionCase):
    """Regresii pentru INVENTORY-002/004/005/006 (#3475-#3478)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create({"name": "Test P2", "is_storable": True})
        cls.product_b = cls.env["product.product"].create({"name": "Test P2 B", "is_storable": True})
        cls.product_c = cls.env["product.product"].create({"name": "Test P2 C", "is_storable": True})
        cls.Line = cls.env["stock.inventory.line"]

    # INVENTORY-002 (#3475)

    def test_return_keeps_fraction_in_move_unit(self):
        """Cantitatea propusa la retur ramane in unitatea miscarii (0.4 duzini, nu 0)."""
        dozen = self.env.ref("uom.product_uom_dozen")
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 100)
        delivery = self.env["stock.picking"].create(
            {
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": dozen.id,
                            "product_uom_qty": 0.4,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )
        delivery.action_confirm()
        delivery.action_assign()
        delivery.move_ids.quantity = 0.4
        delivery.move_ids.picked = True
        delivery.button_validate()
        self.assertEqual(delivery.state, "done")
        wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=delivery.ids, active_id=delivery.id, active_model="stock.picking"
            )
        ).save()
        self.assertAlmostEqual(wizard.product_return_moves.quantity, 0.4)

    # INVENTORY-004 (#3476)

    def _inventory_with_differences(self):
        inventory = self.env["stock.inventory"].create(
            {
                "name": "INV P2",
                "location_ids": [(6, 0, self.stock_location.ids)],
                "product_ids": [(6, 0, (self.product | self.product_b | self.product_c).ids)],
            }
        )
        inventory.action_start()
        lines = {}
        for product, diff in ((self.product, 0.0), (self.product_b, 3.0), (self.product_c, 5.0)):
            line = inventory.line_ids.filtered(lambda li, p=product: li.product_id == p)
            if not line:
                line = self.Line.create(
                    {
                        "inventory_id": inventory.id,
                        "product_id": product.id,
                        "location_id": self.stock_location.id,
                    }
                )
            line.product_qty = line.theoretical_qty + diff
            lines[diff] = line
        return inventory, lines

    def test_search_difference_uses_value(self):
        inventory, lines = self._inventory_with_differences()
        Line = self.Line.with_context(default_inventory_id=inventory.id)
        zero, three, five = lines[0.0], lines[3.0], lines[5.0]

        self.assertEqual(Line.search([("difference_qty", "=", 0)]), zero)
        self.assertEqual(Line.search([("difference_qty", "=", 3)]), three)
        self.assertEqual(Line.search([("difference_qty", "!=", 0)]), three | five)
        self.assertEqual(Line.search([("difference_qty", "!=", 5)]), zero | three)
        self.assertEqual(Line.search([("difference_qty", "in", [0, 5])]), zero | five)
        self.assertEqual(Line.search([("difference_qty", ">", 3)]), five)
        self.assertEqual(Line.search([("difference_qty", "<=", 3)]), zero | three)
        self.assertEqual(Line.search([("difference_qty", "=", False)]), zero)

    def test_search_difference_negative(self):
        inventory, lines = self._inventory_with_differences()
        lines[3.0].product_qty = lines[3.0].theoretical_qty - 2
        Line = self.Line.with_context(default_inventory_id=inventory.id)
        self.assertEqual(Line.search([("difference_qty", "<", 0)]), lines[3.0])
        self.assertEqual(Line.search([("difference_qty", "=", -2)]), lines[3.0])

    # INVENTORY-005 (#3477)

    def test_warehouse_products_action_creates_storable_goods(self):
        action = self.env.ref("deltatech_stock_inventory.action_product_template_warehouse")
        context = safe_eval(action.context)
        template = self.env["product.template"].with_context(**context).create({"name": "WH product"})
        self.assertEqual(template.type, "consu")
        self.assertTrue(template.is_storable)

    def test_inventory_product_contexts_valid(self):
        arch = self.env.ref("deltatech_stock_inventory.view_inventory_form").arch
        arch += self.env.ref("deltatech_stock_inventory.stock_inventory_line_tree").arch
        self.assertNotIn("'default_type': 'product'", arch)

    def test_warehouse_form_on_hand_button_for_storable(self):
        view = self.env.ref("deltatech_stock_inventory.view_product_template_warehouse_form")
        doc = etree.fromstring(view.arch)
        button = doc.xpath("//button[@name='action_open_quants']")[0]
        self.assertEqual(button.get("invisible"), "not is_storable")

    # INVENTORY-006 (#3478)

    def _form_fields(self, user):
        view = self.env.ref("deltatech_stock_inventory.view_product_template_warehouse_form")
        res = (
            self.env["product.template"]
            .with_user(user)
            .with_context(warehouse=self.warehouse.id)
            .get_view(view.id, "form")
        )
        doc = etree.fromstring(res["arch"])
        return {node.get("name") for node in doc.xpath("//field")}

    def test_manual_location_fields_follow_setting(self):
        group = self.env.ref("deltatech_stock_inventory.group_show_manual_location_fields")
        user = self.env["res.users"].create(
            {
                "name": "Stock P2",
                "login": "stock_p2_user",
                "group_ids": [(6, 0, [self.env.ref("stock.group_stock_user").id])],
            }
        )
        user.group_ids -= group
        self.assertFalse(user.has_group("deltatech_stock_inventory.group_show_manual_location_fields"))
        self.assertNotIn("loc_rack", self._form_fields(user))
        user.group_ids |= group
        self.env.registry.clear_cache("templates")
        self.assertIn("loc_rack", self._form_fields(user))
