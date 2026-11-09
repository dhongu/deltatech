"""Livrările din Punctul de vânzare cu „Permite stoc negativ din Punctul de vânzare”.

POS creează livrarea bonului doar cu `pos_session_id` și o validează imediat, într-un
`try/except UserError`; `pos_order_id` se scrie abia după aceea (bon în timp real) sau
deloc (livrarea grupată la închiderea sesiunii). Ocolirea recunoștea livrarea după
`pos_order_id`, deci nu se aplica tocmai bonurilor: livrarea rămânea nevalidată și
stocul nescăzut. O livrare ulterioară (marfa încă în magazin) rămâne supusă regulii.

`point_of_sale` nu e dependență a modulului: testul se sare când nu e instalat.
"""

import unittest

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tests import tagged
from odoo.tests.common import get_db_name

try:
    from odoo.addons.point_of_sale.tests.common import TestPoSCommon
except ImportError:  # point_of_sale lipsește din calea de addon-uri
    TestPoSCommon = None


@tagged("post_install", "-at_install")
class TestNegativePos(TestPoSCommon or unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if TestPoSCommon is None or "pos.order" not in Registry(get_db_name()):
            raise unittest.SkipTest("point_of_sale nu e instalat")
        super().setUpClass()
        cls.env.company.no_negative_stock = True
        cls.stock_location = cls.company_data["default_warehouse"].lot_stock_id

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.config.write({"payment_method_ids": [(6, 0, self.cash_pm1.ids)]})
        self.product = self.create_product("Cablu POS", self.categ_basic, 10.0, 5.0)
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 1.0)

    def _sell(self, qty, **order_args):
        order_data = {
            "pos_order_lines_ui_args": [(self.product, qty)],
            "payments": [(self.cash_pm1, 10.0 * qty)],
        }
        if order_args:
            order_data["customer"] = self.customer
            order_data["pos_order_ui_args"] = order_args
        return next(iter(self._create_orders([order_data]).values()))

    def test_real_time_receipt_bypasses_the_rule(self):
        self.open_new_session()
        order = self._sell(2)
        self.assertEqual(order.picking_ids.state, "done")
        self.assertEqual(self.product.qty_available, -1.0)

    def test_real_time_receipt_blocked_without_bypass(self):
        self.env.company.no_negative_stock_pos_bypass = False
        self.open_new_session()
        order = self._sell(2)
        self.assertNotEqual(order.picking_ids.state, "done")
        self.assertEqual(self.product.qty_available, 1.0)

    def test_session_closing_delivery_bypasses_the_rule(self):
        self.env.company.point_of_sale_update_stock_quantities = "closing"
        session = self.open_new_session()
        self._sell(2)
        session.post_closing_cash_details(20.0)
        session.close_session_from_ui()
        self.assertEqual(session.picking_ids.state, "done")
        self.assertEqual(self.product.qty_available, -1.0)

    def test_ship_later_delivery_keeps_the_rule(self):
        self.config.ship_later = True
        self.open_new_session()
        shipping_date = fields.Date.today() + relativedelta(days=1)
        order = self._sell(2, shipping_date=fields.Date.to_string(shipping_date))
        picking = order.picking_ids
        self.assertNotEqual(picking.state, "done")
        picking.move_ids.quantity = 2.0
        picking.move_ids.picked = True
        with self.assertRaises(UserError):
            picking._action_done()
        self.assertEqual(self.product.qty_available, 1.0)
