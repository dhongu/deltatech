# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestSOType(TransactionCase):
    def setUp(self):
        super(TestSOType, self).setUp()
        values = {
            "name": "Type 1",
        }
        self.type1 = self.env["sale.order.type"].create(values)
        self.type1.write({"is_default": True})
        values = {
            "name": "Type 2",
        }
        self.type2 = self.env["sale.order.type"].create(values)

    def test_update_saleorder(self):
        test_saleorder = self.env["sale.order"].create(
            {
                "partner_id": 1,
            }
        )
        test_saleorder.write({"so_type": self.type1.id})
