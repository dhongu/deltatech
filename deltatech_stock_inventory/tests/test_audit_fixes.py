# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestInventoryAuditFixes(TransactionCase):
    """Defectele gasite la auditul fisei consultant (sectiunea 11, Limitari cunoscute)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_str("stock.use_inventory_price", "True")
        cls.location = cls.env["stock.location"].create({"name": "Audit Loc A", "usage": "internal"})
        cls.location_b = cls.env["stock.location"].create({"name": "Audit Loc B", "usage": "internal"})

    def _product(self, cost_method, price, name=None):
        categ = self.env["product.category"].create(
            {"name": f"Audit {cost_method}", "property_cost_method": cost_method}
        )
        return self.env["product.product"].create(
            {
                "name": name or f"Audit {cost_method} product",
                "is_storable": True,
                "categ_id": categ.id,
                "standard_price": price,
            }
        )

    def _receive(self, product, qty, location=None):
        """Stoc initial printr-o receptie reala, la costul produsului.

        In 20.0 costul mediu (AVCO) se recalculeaza reluand miscarile de stoc
        (product.product._run_avco), nu incremental pe qty_available ca in 19.0; un stoc
        pus direct pe quant, fara miscare, ar fi invizibil pentru reluare.
        """
        move = self.env["stock.move"].create(
            {
                "product_id": product.id,
                "uom_id": product.uom_id.id,
                "product_uom_qty": qty,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": (location or self.location).id,
            }
        )
        move._action_confirm()
        move.quantity = qty
        move.picked = True
        move._action_done()

    def _inventory(self, products, locations=None, name="INV/AUDIT", exhausted=False):
        inventory = self.env["stock.inventory"].create(
            {
                "name": name,
                "location_ids": [(6, 0, (locations or self.location).ids)],
                "product_ids": [(6, 0, products.ids)],
                "exhausted": exhausted,
            }
        )
        inventory.action_start()
        return inventory

    # 1. Pretul de pe linie nu reevalueaza stocul existent

    def test_average_surplus_at_line_price_without_revaluation(self):
        product = self._product("average", 10.0)
        self._receive(product, 10.0)
        inventory = self._inventory(product)
        line = inventory.line_ids
        line.write({"product_qty": 15.0, "standard_price": 20.0})
        values_before = self.env["product.value"].search_count([("product_id", "=", product.id)])

        inventory.action_validate()

        move = inventory.move_ids
        self.assertEqual(move.value, 100.0, "Plusul de 5 buc intra la pretul liniei (20)")
        self.assertEqual(
            self.env["product.value"].search_count([("product_id", "=", product.id)]),
            values_before,
            "Validarea nu trebuie sa creeze reevaluare (product.value)",
        )
        # Cost mediu ponderat: (10 x 10 + 5 x 20) / 15, nu 20 (reevaluarea stocului existent)
        self.assertAlmostEqual(product.standard_price, 200.0 / 15, places=2)
        self.assertAlmostEqual(product.total_value, 200.0, places=2)

    def test_average_minus_keeps_cost(self):
        product = self._product("average", 10.0)
        self._receive(product, 10.0)
        inventory = self._inventory(product)
        inventory.line_ids.write({"product_qty": 8.0, "standard_price": 50.0})
        inventory.action_validate()
        self.assertEqual(product.standard_price, 10.0)
        self.assertEqual(abs(inventory.move_ids.value), 20.0, "Minusul iese la costul mediu, nu la pretul liniei")

    def test_fifo_surplus_layer_at_line_price(self):
        product = self._product("fifo", 10.0)
        self._receive(product, 10.0)
        inventory = self._inventory(product)
        inventory.line_ids.write({"product_qty": 12.0, "standard_price": 30.0})
        inventory.action_validate()
        self.assertEqual(inventory.move_ids.value, 60.0)

    def test_parameter_off_ignores_line_price(self):
        self.env["ir.config_parameter"].sudo().set_str("stock.use_inventory_price", "False")
        product = self._product("average", 10.0)
        self._receive(product, 10.0)
        inventory = self._inventory(product)
        inventory.line_ids.write({"product_qty": 15.0, "standard_price": 20.0})
        inventory.action_validate()
        self.assertEqual(inventory.move_ids.value, 50.0, "Cu parametrul oprit, plusul intra la costul produsului")
        self.assertEqual(product.standard_price, 10.0)

    def test_parameter_off_ignores_line_price_on_zero_theoretical(self):
        """Parametrul decide si pe liniile cu scriptic 0 (inainte costul se scria oricum)."""
        self.env["ir.config_parameter"].sudo().set_str("stock.use_inventory_price", "False")
        product = self._product("standard", 10.0)
        inventory = self._inventory(product, exhausted=True)
        inventory.line_ids.write({"product_qty": 3.0, "standard_price": 40.0})
        inventory.action_validate()
        self.assertEqual(product.standard_price, 10.0)
        self.assertEqual(inventory.move_ids.value, 30.0)

    def test_standard_zero_theoretical_without_stock_sets_cost(self):
        product = self._product("standard", 10.0)
        inventory = self._inventory(product, exhausted=True)
        line = inventory.line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.theoretical_qty, 0.0)
        line.write({"product_qty": 3.0, "standard_price": 40.0})
        inventory.action_validate()
        self.assertEqual(product.standard_price, 40.0, "Produs fara stoc: pretul liniei devine costul standard")
        self.assertEqual(inventory.move_ids.value, 120.0)

    def test_standard_zero_theoretical_with_stock_elsewhere_keeps_cost(self):
        product = self._product("standard", 10.0)
        self._receive(product, 7.0, self.location_b)
        inventory = self._inventory(product, exhausted=True)
        line = inventory.line_ids.filtered(lambda ln: ln.location_id == self.location)
        self.assertEqual(line.theoretical_qty, 0.0)
        line.write({"product_qty": 3.0, "standard_price": 40.0})
        inventory.action_validate()
        self.assertEqual(product.standard_price, 10.0, "Stocul din alta locatie nu se reevalueaza")
        self.assertAlmostEqual(product.total_value, 100.0, places=2)

    def test_standard_with_stock_keeps_cost(self):
        product = self._product("standard", 10.0)
        self._receive(product, 5.0)
        inventory = self._inventory(product)
        inventory.line_ids.write({"product_qty": 6.0, "standard_price": 40.0})
        inventory.action_validate()
        self.assertEqual(product.standard_price, 10.0)
        self.assertEqual(inventory.move_ids.value, 10.0)

    # 2. Mesajul pentru cantitate negativa

    def test_negative_quantity_user_error(self):
        product = self._product("standard", 10.0, name="Negative Audit Product")
        self._receive(product, 2.0)
        inventory = self._inventory(product)
        inventory.line_ids.product_qty = -1.0
        with self.assertRaisesRegex(UserError, "Negative Audit Product - qty: -1"):
            inventory.action_validate()

    # 3. Include Exhausted Products fara produse selectate

    def test_exhausted_products_without_product_filter(self):
        product = self._product("standard", 10.0)
        inventory = self.env["stock.inventory"].create(
            {"name": "INV/EXH", "location_ids": [(6, 0, self.location.ids)], "exhausted": True}
        )
        vals = inventory._get_exhausted_inventory_lines_vals(set())
        self.assertIn((product.id, self.location.id), {(v["product_id"], v["location_id"]) for v in vals})

    # 4. Mesajul de confirmare a cantitatii

    def test_confirm_inventory_message_has_location(self):
        product = self._product("standard", 10.0)
        self._receive(product, 4.0)
        quant = self.env["stock.quant"].search(
            [("product_id", "=", product.id), ("location_id", "=", self.location.id)]
        )
        quant.action_confirm_inventory()
        body = product.product_tmpl_id.message_ids[:1].body
        self.assertIn("Audit Loc A", body)
        self.assertNotIn("%(location)", body)

    # 5. Raportul de diferente pe mai multe locatii

    def test_diff_report_minus_lines_filtered_by_location(self):
        minus_product = self._product("standard", 10.0, name="Minus Audit Product")
        plus_product = self._product("standard", 10.0, name="Plus Audit Product")
        self._receive(minus_product, 5.0, self.location)
        self._receive(plus_product, 5.0, self.location_b)
        inventory = self._inventory(minus_product | plus_product, self.location | self.location_b)
        inventory.line_ids.filtered(lambda ln: ln.product_id == minus_product).product_qty = 2.5
        inventory.line_ids.filtered(lambda ln: ln.product_id == plus_product).product_qty = 6.0

        html = (
            self.env["ir.actions.report"]
            ._render_qweb_html("deltatech_stock_inventory.report_inventory_diff", inventory.ids)[0]
            .decode()
            .replace("\ufeff", "")
        )
        self.assertEqual(html.count("Minus Audit Product"), 1, "Minusul apare doar sub locatia lui")
        self.assertIn("-2.50", html, "Diferenta cantitativa pastreaza zecimalele")
        self.assertNotIn("text-right", html)

    # 6. Data implicita a wizardului de unire

    def test_merge_wizard_default_date_is_current(self):
        with freeze_time("2031-03-04 10:00:00"):
            defaults = self.env["stock.inventory.merge"].default_get(["date"])
        self.assertEqual(str(defaults["date"]), "2031-03-04 10:00:00")

    # 7. Referinta miscarii = numele documentului

    def test_move_reference_is_inventory_name(self):
        product = self._product("standard", 10.0)
        self._receive(product, 5.0)
        inventory = self._inventory(product, name="INV/AUDIT/REF")
        inventory.line_ids.product_qty = 3.0
        inventory.action_validate()
        self.assertEqual(inventory.move_ids.reference, "INV/AUDIT/REF")

    def test_move_reference_uses_sequence_name(self):
        """Documentul numit "/" primeste numarul din secventa inainte de generarea miscarilor."""
        product = self._product("standard", 10.0)
        self._receive(product, 5.0)
        inventory = self._inventory(product, name="/")
        inventory.line_ids.product_qty = 3.0
        inventory.action_validate()
        self.assertNotEqual(inventory.name, "/")
        self.assertEqual(inventory.move_ids.reference, inventory.name)
