from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestPosStockShops(TestPoSCommon):
    """The figures of the other shops are read on the server and travel with the session."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        cls.own_warehouse = cls.config.picking_type_id.warehouse_id
        Warehouse = cls.env["stock.warehouse"]
        cls.shop_b = Warehouse.create({"name": "Shop B", "code": "SHB", "company_id": cls.company.id})
        cls.shop_c = Warehouse.create({"name": "Shop C", "code": "SHC", "company_id": cls.company.id})
        cls.central = Warehouse.create({"name": "Central", "code": "CEN", "company_id": cls.company.id})
        # Shop B and shop C have a register, the central warehouse does not.
        for warehouse in (cls.shop_b, cls.shop_c):
            cls.env["pos.config"].create(
                {
                    "name": f"POS {warehouse.name}",
                    "company_id": cls.company.id,
                    "picking_type_id": warehouse.pos_type_id.id,
                }
            )
        cls.config.write({"display_stock": True, "display_shop_stock": True})

        cls.product = cls.env["product.product"].create(
            {"name": "Shop Stock Product", "is_storable": True, "available_in_pos": True}
        )
        cls.template = cls.product.product_tmpl_id
        Quant = cls.env["stock.quant"]
        Quant._update_available_quantity(cls.product, cls.own_warehouse.lot_stock_id, 2)
        Quant._update_available_quantity(cls.product, cls.shop_b.lot_stock_id, 5)
        # A sub-location of the shop counts for the shop.
        shelf = cls.env["stock.location"].create({"name": "Shelf", "location_id": cls.shop_b.lot_stock_id.id})
        Quant._update_available_quantity(cls.product, shelf, 1)
        Quant._update_available_quantity(cls.product, cls.central.lot_stock_id, 100)

    def _read_template(self, config=None):
        config = config or self.config
        return self.env["product.template"]._load_pos_data_read(self.template, config)[0]

    def test_default_shops_are_the_other_registers(self):
        self.assertEqual(self.config._get_stock_shop_warehouses(), self.shop_b | self.shop_c)
        self.assertEqual(
            self.config.stock_shop_list,
            [{"id": self.shop_b.id, "name": "Shop B"}, {"id": self.shop_c.id, "name": "Shop C"}]
            if self.shop_b.sequence <= self.shop_c.sequence
            else [{"id": self.shop_c.id, "name": "Shop C"}, {"id": self.shop_b.id, "name": "Shop B"}],
        )

    def test_chosen_shops_replace_the_default_and_never_include_this_shop(self):
        self.config.stock_shop_warehouse_ids = self.central | self.own_warehouse
        self.assertEqual(self.config._get_stock_shop_warehouses(), self.central)

    def test_switched_off_loads_nothing(self):
        self.config.display_shop_stock = False
        self.assertFalse(self.config.stock_shop_list)
        fields = self.env["product.template"]._load_pos_data_fields(self.config)
        self.assertNotIn("pos_shop_stock", fields)
        self.config.write({"display_shop_stock": True, "display_stock": False})
        self.assertFalse(self.config._get_stock_shop_warehouses())

    def test_stock_per_shop_is_loaded_with_the_product(self):
        fields = self.env["product.template"]._load_pos_data_fields(self.config)
        self.assertIn("pos_shop_stock", fields)
        data = self._read_template()
        # Shop C has nothing, the central warehouse is not a shop, this shop is on the badge.
        self.assertEqual(data["pos_shop_stock"], {str(self.shop_b.id): 6.0})
        self.assertEqual(data["qty_available"], 2.0)

    def test_available_quantity_subtracts_reservations(self):
        self.config.stock_badge_quantity = "available"
        quant = self.env["stock.quant"].search(
            [("product_id", "=", self.product.id), ("location_id", "=", self.shop_b.lot_stock_id.id)]
        )
        quant.reserved_quantity = 3
        self.assertEqual(self._read_template()["pos_shop_stock"], {str(self.shop_b.id): 3.0})

    def test_other_shops_are_read_without_stock_rights(self):
        # A cashier may not read the quants of another warehouse; the shop figures still load.
        cashier = new_test_user(
            self.env,
            login="shop_stock_cashier",
            groups="point_of_sale.group_pos_user",
            company_id=self.company.id,
            company_ids=self.company.ids,
        )
        self.env.invalidate_all()
        # The core read of the POS session is not ours; what is ours is reading the other
        # shops (picking types, warehouses, quants) on behalf of a cashier.
        warehouses = self.config.with_user(cashier)._get_stock_shop_warehouses()
        self.assertEqual(warehouses, self.shop_b | self.shop_c)
        template = self.template.with_user(cashier).with_context(pos_shop_warehouse_ids=warehouses.ids)
        self.assertEqual(template.pos_shop_stock, {str(self.shop_b.id): 6.0})

    def test_outside_the_pos_the_field_stays_empty(self):
        self.assertFalse(self.template.pos_shop_stock)

    def test_variants_are_summed_on_the_template(self):
        attribute = self.env["product.attribute"].create(
            {"name": "Colour", "value_ids": [(0, 0, {"name": "Red"}), (0, 0, {"name": "Blue"})]}
        )
        template = self.env["product.template"].create(
            {
                "name": "Coloured Product",
                "is_storable": True,
                "available_in_pos": True,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, attribute.value_ids.ids)]})
                ],
            }
        )
        for variant, qty in zip(template.product_variant_ids, (4, 7), strict=True):
            self.env["stock.quant"]._update_available_quantity(variant, self.shop_c.lot_stock_id, qty)
        data = self.env["product.template"]._load_pos_data_read(template, self.config)[0]
        self.assertEqual(data["pos_shop_stock"], {str(self.shop_c.id): 11.0})

    def test_a_sale_in_another_shop_reaches_this_register(self):
        self.config.open_ui()
        self.config.current_session_id.set_opening_control(0, "")
        sent = []

        def _notify(config, name, message):
            sent.append((config, name, message))

        with patch.object(type(self.config), "_notify", _notify):
            self.env["stock.quant"]._update_available_quantity(self.product, self.shop_b.lot_stock_id, -2)
        payloads = [msg for config, name, msg in sent if config == self.config and name == "STOCK_SYNCHRONISATION"]
        self.assertTrue(payloads)
        self.assertEqual(payloads[-1]["product.template"][0]["pos_shop_stock"], {str(self.shop_b.id): 4.0})
