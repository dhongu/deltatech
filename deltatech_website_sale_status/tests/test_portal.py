# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from unittest.mock import patch

from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.deltatech_website_sale_status.controllers.portal import CustomerPortal

FILTERS = (
    "all",
    "open_order",
    "closed_order",
    "placed",
    "in_process",
    "waiting",
    "postponed",
    "to_be_delivery",
    "in_delivery",
    "delivered",
    "cancel",
)


@tagged("post_install", "-at_install")
class TestPortalOrders(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_login = "wss_portal_user"
        cls.portal_user = new_test_user(cls.env, login=cls.portal_login, groups="base.group_portal")
        cls.partner = cls.portal_user.partner_id
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        storable = cls.env["product.product"].create(
            {"name": "Portal Storable", "type": "consu", "is_storable": True, "list_price": 10}
        )
        no_stock = cls.env["product.product"].create(
            {"name": "Portal No Stock", "type": "consu", "is_storable": True, "list_price": 10}
        )
        service = cls.env["product.product"].create({"name": "Portal Service", "type": "service", "list_price": 10})
        cls.env["stock.quant"]._update_available_quantity(storable, cls.warehouse.lot_stock_id, 10)

        def make_order(product, qty):
            order = cls.env["sale.order"].create(
                {
                    "partner_id": cls.partner.id,
                    "warehouse_id": cls.warehouse.id,
                    "order_line": [(0, 0, {"product_id": product.id, "product_uom_qty": qty})],
                }
            )
            order.action_confirm()
            return order

        cls.order_to_deliver = make_order(storable, 2)
        cls.order_waiting = make_order(no_stock, 5)
        cls.order_delivered = make_order(service, 1)
        cls.order_canceled = make_order(service, 1)
        cls.order_canceled._action_cancel()
        cls.quotation = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [(0, 0, {"product_id": service.id, "product_uom_qty": 1})],
            }
        )
        cls.quotation.action_quotation_sent()

    def setUp(self):
        super().setUp()
        self.authenticate(self.portal_login, self.portal_login)

    def _get(self, url):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200, url)
        return response.text

    def test_stages_of_orders(self):
        self.assertEqual(self.order_to_deliver.stage, "to_be_delivery")
        self.assertEqual(self.order_waiting.stage, "waiting")
        self.assertEqual(self.order_delivered.stage, "delivered")
        self.assertEqual(self.order_canceled.stage, "canceled")

    def test_my_orders_default(self):
        html = self._get("/my/orders")
        for order in (self.order_to_deliver, self.order_waiting, self.order_delivered):
            self.assertIn(order.name, html)
        self.assertIn("bg-success", html)
        self.assertIn("bg-danger", html)
        self.assertIn("bg-info", html)
        self.assertIn("filterby=all", html)
        self.assertIn("Open Orders", html)

    def test_my_orders_filters(self):
        expected = {
            "open_order": (self.order_to_deliver, self.order_waiting),
            "closed_order": (self.order_delivered, self.order_canceled),
            "waiting": (self.order_waiting,),
            "to_be_delivery": (self.order_to_deliver,),
            "delivered": (self.order_delivered,),
            "cancel": (self.order_canceled,),
            # the standard list holds confirmed orders only
            "all": (self.order_to_deliver, self.order_waiting, self.order_delivered),
        }
        all_orders = self.order_to_deliver | self.order_waiting | self.order_delivered | self.order_canceled
        for filterby in FILTERS:
            html = self._get(f"/my/orders?filterby={filterby}")
            shown = expected.get(filterby)
            for order in all_orders:
                if shown is not None and order in shown:
                    self.assertIn(order.name, html, filterby)
                else:
                    self.assertNotIn(order.name, html, filterby)

    def test_my_orders_unknown_filter(self):
        html = self._get("/my/orders?filterby=unknown_filter")
        self.assertIn(self.order_waiting.name, html)

    def test_my_orders_sort_by_stage(self):
        html = self._get("/my/orders?sortby=order_stage")
        self.assertIn("Order Stage", html)
        self.assertIn(self.order_delivered.name, html)

    def test_my_orders_pager_keeps_filter(self):
        with patch.object(CustomerPortal, "_items_per_page", 1):
            html = self._get("/my/orders/page/2?filterby=open_order")
        self.assertIn("filterby=open_order", html)

    def test_my_quotes(self):
        html = self._get("/my/quotes")
        self.assertIn(self.quotation.name, html)
        self.assertIn("Status", html)

    def test_my_quotes_empty_filter(self):
        html = self._get("/my/quotes?filterby=")
        self.assertIn(self.quotation.name, html)

    def test_fix_pager_filer(self):
        pager = {
            key: {"url": "/my/orders?sortby=date"}
            for key in ("page", "page_first", "page_previous", "page_next", "page_last")
        }
        pager["pages"] = [{"url": "/my/orders/page/2?sortby=date", "num": 2}, {"url": False, "num": 3}]
        result = CustomerPortal().fix_pager_filer(pager, "delivered")
        self.assertEqual(result["page"]["url"], "/my/orders?sortby=date&filterby=delivered")
        self.assertEqual(result["pages"][0]["url"], "/my/orders/page/2?sortby=date&filterby=delivered")
        self.assertFalse(result["pages"][1]["url"])
