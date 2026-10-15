# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAlternativeDropdownDisplay(TransactionCase):
    """Product name in the selection dropdown: classic [code] name and stock."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product = cls.env["product.product"].create(
            {"name": "Filter battery", "default_code": "CP082788", "is_storable": True, "uom_id": cls.uom_unit.id}
        )
        cls.service = cls.env["product.product"].create({"name": "Labour", "default_code": "MAN01", "type": "service"})
        cls.no_code = cls.env["product.product"].create({"name": "No code part", "is_storable": True})
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.env.ref("stock.stock_location_stock"), 12)

    def _set(self, code_first, show_qty):
        self.ICP.set_param("alternative.dropdown_code_first", str(code_first))
        self.ICP.set_param("alternative.dropdown_show_qty", str(show_qty))

    def _formatted(self, product):
        return product.with_context(formatted_display_name=True).display_name

    def _stock(self, qty):
        return f"Stock: {qty} {self.uom_unit.name}"

    def test_default_keeps_odoo_format(self):
        self._set(False, False)
        self.assertEqual(self._formatted(self.product), "Filter battery\t--CP082788--")

    def test_code_first(self):
        self._set(True, False)
        self.assertEqual(self._formatted(self.product), "[CP082788] Filter battery")
        self.assertEqual(self._formatted(self.no_code), "No code part")

    def test_code_first_with_stock(self):
        self._set(True, True)
        self.assertEqual(self._formatted(self.product), f"[CP082788] Filter battery\t--{self._stock('12.00')}--")
        self.assertEqual(self._formatted(self.no_code), f"No code part\t--{self._stock('0.00')}--")
        # services have no stock
        self.assertEqual(self._formatted(self.service), "[MAN01] Labour")

    def test_stock_with_odoo_format(self):
        self._set(False, True)
        self.assertEqual(self._formatted(self.product), f"Filter battery\t--CP082788 · {self._stock('12.00')}--")

    def test_plain_name_unchanged(self):
        self._set(True, True)
        self.assertEqual(self.product.display_name, "[CP082788] Filter battery")

    def test_web_name_search(self):
        self._set(True, True)
        res = self.env["product.product"].web_name_search("CP082788", {"display_name": {}})
        self.assertEqual(res[0]["__formatted_display_name"], f"[CP082788] Filter battery\t--{self._stock('12.00')}--")
