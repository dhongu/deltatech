from odoo.exceptions import AccessError
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

    # SALECOST-001 (#3460): costul se normalizează pe companie, UM și monedă
    def test_cost_of_goods_line_uom(self):
        """Costul e pe UM de bază; o linie în duzini trebuie convertită."""
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "product_uom_qty": 1,
                            "product_uom_id": self.env.ref("uom.product_uom_dozen").id,
                            "price_unit": 240.0,
                        },
                    ),
                ],
            }
        )
        order.action_confirm()
        # 1 duzină × 12 × 10.0 = 120.0
        self.assertAlmostEqual(order.cost_of_goods, 120.0)
        order.cost_of_goods = 0.0
        self.env["sale.order"].calculate_cost_of_goods_for_confirmed_orders()
        self.assertAlmostEqual(order.cost_of_goods, 120.0)

    def test_cost_of_goods_order_currency(self):
        """Costul în moneda companiei se convertește în moneda comenzii."""
        company = self.env.company
        currency = self.env["res.currency"].create({"name": "TSC", "symbol": "T$", "rounding": 0.01})
        self.env["res.currency.rate"].create(
            {"name": "2000-01-01", "rate": 2.0, "currency_id": currency.id, "company_id": company.id}
        )
        pricelist = self.env["product.pricelist"].create({"name": "TSC pricelist", "currency_id": currency.id})
        order = self._create_sale_order()
        order.pricelist_id = pricelist
        self.assertEqual(order.currency_id, currency)
        order.action_confirm()
        # (10 × 3 + 5 × 2) = 40.0 în moneda companiei → 80.0 în TSC
        self.assertAlmostEqual(order.cost_of_goods, 80.0)

    def test_cost_of_goods_order_company(self):
        """Costul se citește pe compania comenzii, nu pe compania activă."""
        company_b = self.env["res.company"].create(
            {"name": "Company B SCP", "currency_id": self.env.company.currency_id.id}
        )
        self.product1.with_company(company_b).standard_price = 50.0
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": company_b.id,
                "order_line": [(0, 0, {"product_id": self.product1.id, "product_uom_qty": 2, "price_unit": 60.0})],
            }
        )
        self.assertNotEqual(self.env.company, company_b)
        order.action_confirm()
        self.assertAlmostEqual(order.cost_of_goods, 100.0)

    # SALECOST-002 (#3461): câmpul e protejat de grupul de vizibilitate
    def test_cost_of_goods_field_group(self):
        """Un vânzător din afara grupului nu poate citi costul, dar poate confirma comanda."""
        salesman = self.env["res.users"].create(
            {
                "name": "Salesman SCP",
                "login": "salesman_scp",
                "group_ids": [(6, 0, [self.env.ref("sales_team.group_sale_salesman_all_leads").id])],
            }
        )
        order = self._create_sale_order()
        order_as_user = order.with_user(salesman)
        with self.assertRaises(AccessError):
            order_as_user.read(["cost_of_goods"])
        order_as_user.action_confirm()
        self.assertAlmostEqual(order.cost_of_goods, 40.0)
        salesman.group_ids = [(4, self.env.ref("deltatech_sale_cost_product.group_view_cost_on_sale").id)]
        self.assertAlmostEqual(order.with_user(salesman).read(["cost_of_goods"])[0]["cost_of_goods"], 40.0)

    def test_copy_order_without_group(self):
        """Un vânzător din afara grupului poate duplica o comandă confirmată, fără a moșteni costul."""
        salesman = self.env["res.users"].create(
            {
                "name": "Salesman copy SCP",
                "login": "salesman_copy_scp",
                "group_ids": [(6, 0, [self.env.ref("sales_team.group_sale_salesman_all_leads").id])],
            }
        )
        order = self._create_sale_order()
        order.action_confirm()
        self.assertAlmostEqual(order.cost_of_goods, 40.0)
        new_order = order.with_user(salesman).copy()
        self.assertEqual(new_order.state, "draft")
        self.assertEqual(new_order.sudo().cost_of_goods, 0.0)
