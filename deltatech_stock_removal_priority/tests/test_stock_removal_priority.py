# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "deltatech_stock_removal_priority")
class TestStockRemovalPriority(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "product", "categ_id": cls.env.ref("product.product_category_all").id}
        )

        cls.loc_1 = cls.env["stock.location"].create({"name": "Loc 1", "location_id": cls.stock_location.id})
        cls.loc_2 = cls.env["stock.location"].create({"name": "Loc 2", "location_id": cls.stock_location.id})

    def test_01_quant_priority_from_putaway(self):
        """Test ca prioritatea cuantului este luata din regula de putaway"""
        # Cream o regula de putaway
        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product.id,
                "location_in_id": self.loc_1.id,
                "location_out_id": self.loc_2.id,
                "sequence": 5,
            }
        )

        # Cream un cuant
        quant = self.env["stock.quant"].create(
            {"product_id": self.product.id, "location_id": self.loc_1.id, "inventory_quantity": 10}
        )
        quant.action_apply_inventory()

        # Prioritatea ar trebui sa fie sequence-ul regulii de putaway (5)
        self.assertEqual(quant.removal_priority, 5)

    def test_02_removal_strategy_priority(self):
        """Test strategia de eliminare 'Priority'"""
        # Verificam ca metoda de domain order returneaza valorile asteptate
        domain = [("product_id", "=", self.product.id)]
        new_domain, order = self.env["stock.quant"]._get_removal_strategy_domain_order(domain, "priority", 100)

        self.assertIn(("removal_priority", ">", 0), new_domain)
        self.assertEqual(order, "removal_priority, location_id, id")

        # Verificam sort_key
        key, reverse = self.env["stock.quant"]._get_removal_strategy_sort_key("priority")
        self.assertFalse(reverse)

        # Cream un obiect fals pentru a testa cheia de sortare
        class MockQuant:
            def __init__(self, priority, name, id):
                self.removal_priority = priority
                self.location_id = type("obj", (object,), {"complete_name": name})
                self.id = id

        q1 = MockQuant(10, "A", 1)
        q2 = MockQuant(5, "B", 2)

        # q2 are prioritate mai mica (deci mai importanta), deci ar trebui sa fie primul
        self.assertLess(key(q2), key(q1))
