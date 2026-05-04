from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleCostProduct(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "consu",
                "standard_price": 10.0,
                "list_price": 20.0,
            }
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "consu",
                "standard_price": 5.0,
                "list_price": 15.0,
            }
        )

    def _create_sale_order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "product_uom_qty": 3,
                            "price_unit": 20.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product2.id,
                            "product_uom_qty": 2,
                            "price_unit": 15.0,
                        },
                    ),
                ],
            }
        )
        return order

    def test_cost_of_goods_on_confirm(self):
        """La confirmarea comenzii, cost_of_goods trebuie calculat corect."""
        order = self._create_sale_order()
        self.assertEqual(order.cost_of_goods, 0.0)

        order.action_confirm()

        # product1: 10.0 * 3 = 30.0, product2: 5.0 * 2 = 10.0 => total = 40.0
        expected_cost = (self.product1.standard_price * 3) + (self.product2.standard_price * 2)
        self.assertAlmostEqual(order.cost_of_goods, expected_cost)

    def test_cost_of_goods_not_calculated_on_draft(self):
        """cost_of_goods nu trebuie modificat dacă comanda rămâne în draft."""
        order = self._create_sale_order()
        self.assertEqual(order.cost_of_goods, 0.0)
        order.write({"note": "test"})
        self.assertEqual(order.cost_of_goods, 0.0)

    def test_calculate_cost_of_goods_for_confirmed_orders(self):
        """Metoda de recalculare trebuie să actualizeze cost_of_goods pentru comenzile confirmate."""
        order = self._create_sale_order()
        order.action_confirm()

        # Modificăm manual cost_of_goods pentru a simula o valoare incorectă
        order.cost_of_goods = 0.0

        # Apelăm metoda de recalculare
        self.env["sale.order"].calculate_cost_of_goods_for_confirmed_orders()

        expected_cost = (self.product1.standard_price * 3) + (self.product2.standard_price * 2)
        self.assertAlmostEqual(order.cost_of_goods, expected_cost)

    def test_cost_of_goods_with_zero_price(self):
        """Produsele cu standard_price = 0 nu trebuie să afecteze calculul."""
        product_free = self.env["product.product"].create(
            {
                "name": "Product Free",
                "type": "consu",
                "standard_price": 0.0,
                "list_price": 5.0,
            }
        )
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "product_uom_qty": 2,
                            "price_unit": 20.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": product_free.id,
                            "product_uom_qty": 5,
                            "price_unit": 5.0,
                        },
                    ),
                ],
            }
        )
        order.action_confirm()

        expected_cost = self.product1.standard_price * 2  # 10.0 * 2 = 20.0
        self.assertAlmostEqual(order.cost_of_goods, expected_cost)
