from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged("post_install", "-at_install")
class TestPosExtraLine(TestPointOfSaleHttpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.deposit = cls.env["product.product"].create(
            {"name": "Bottle Deposit", "available_in_pos": True, "list_price": 0.5, "taxes_id": False}
        )
        cls.water = cls.env["product.template"].create(
            {
                "name": "Bottled Water",
                "available_in_pos": True,
                "list_price": 2.0,
                "taxes_id": False,
                "extra_product_id": cls.deposit.id,
                "extra_qty": 2.0,
            }
        )

    def test_extra_fields_loaded_in_pos(self):
        """The POS needs the extra product configuration on the template to add the extra line."""
        fields = self.env["product.template"]._load_pos_data_fields(self.main_pos_config.id)
        self.assertTrue({"extra_product_id", "extra_percent", "extra_qty"} <= set(fields))

    def test_extra_line_follows_main_line(self):
        self.start_pos_tour("DeltatechExtraLinePosTour")

    def test_cancelled_main_line_adds_no_extra(self):
        """POSEXTRA-001: no extra line when the main product addition is cancelled."""
        chair = self.env["product.template"].search(
            [("name", "=", "Configurable Chair"), ("available_in_pos", "=", True)], limit=1
        )
        self.assertTrue(chair)
        chair.write({"extra_product_id": self.deposit.id, "extra_qty": 1.0})
        self.start_pos_tour("DeltatechExtraLinePosCancelTour")

    def test_return_preset_extra_line_is_negative(self):
        """POSEXTRA-003: the first extra line follows the quantity of the main line."""
        preset = self.env["pos.preset"].create({"name": "Return", "is_return": True})
        self.main_pos_config.write(
            {
                "use_presets": True,
                "default_preset_id": preset.id,
                "available_preset_ids": [(6, 0, preset.ids)],
            }
        )
        self.start_pos_tour("DeltatechExtraLinePosReturnTour")
