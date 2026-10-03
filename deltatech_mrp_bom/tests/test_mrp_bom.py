# Part of Odoo. See LICENSE file for full copyright and licensing details.

from freezegun import freeze_time

from odoo import Command, fields

from odoo.addons.mrp.tests.common import TestMrpCommon


@freeze_time(fields.Date.today())
class TestBoM(TestMrpCommon):
    # Odoo 20: testele TestMrpCommon rulează cu un utilizator de test (doar mrp.group_mrp_user)
    _test_user_groups = (
        "product.group_product_manager",
        "mrp.group_mrp_manager",
        "uom.group_uom",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.group_user").write({"implied_ids": [(4, cls.env.ref("product.group_product_variant").id)]})

    def test_10_variants(self):
        test_bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.product_7_template.id,
                "uom_id": self.uom_unit.id,
                "product_qty": 4.0,
                "type": "normal",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_2.id,
                            "product_qty": 2,
                        }
                    ),
                ],
            }
        )
        product = self.env["product.template"].create({"name": "Test Product", "is_storable": True})

        test_bom.product_tmpl_id = product.id
        test_bom.onchange_product_tmpl_id()
        self.assertEqual(test_bom.uom_id, product.uom_id)
        self.assertFalse(test_bom.product_id)
