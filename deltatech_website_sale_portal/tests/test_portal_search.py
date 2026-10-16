# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from lxml import html

from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.portal.controllers.portal import CustomerPortal


@tagged("post_install", "-at_install")
class TestPortalSearch(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = new_test_user(
            cls.env, login="wsp_portal", password="wsp_portal", groups="base.group_portal", name="WSP Portal"
        )
        partner = cls.portal_user.partner_id
        product = cls.env["product.product"].create({"name": "WSP Product", "list_price": 10})
        order_model = cls.env["sale.order"]
        vals = []
        for i in range(3):
            vals.append(
                {
                    "partner_id": partner.id,
                    "client_order_ref": f"WSPREF-{i}",
                    "order_line": [(0, 0, {"product_id": product.id, "product_uom_qty": 1})],
                }
            )
        for i in range(3):
            vals.append(
                {
                    "partner_id": partner.id,
                    "client_order_ref": f"OTHER-{i}",
                    "order_line": [(0, 0, {"product_id": product.id, "product_uom_qty": 1})],
                }
            )
        cls.orders = order_model.create(vals)
        cls.orders.write({"state": "sale"})

    def _get_page(self, url):
        self.authenticate("wsp_portal", "wsp_portal")
        with patch.object(CustomerPortal, "_items_per_page", 2):
            response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        return html.fromstring(response.content)

    def test_pager_keeps_search(self):
        doc = self._get_page("/my/orders?search=WSPREF&search_in=all")
        links = [a.get("href") for a in doc.xpath("//ul[contains(@class, 'pagination')]//a[@href]")]
        page2 = [link for link in links if "/page/2" in link]
        self.assertTrue(page2, "The search result must have a second page")
        for link in page2:
            self.assertIn("search=WSPREF", link)
            self.assertIn("search_in=all", link)
        # second page holds only the remaining matching order
        doc = self._get_page(page2[0])
        rows = doc.xpath("//table//tr[td]")
        self.assertEqual(len(rows), 1)
        self.assertIn("WSPREF", rows[0].text_content())

    def test_search_input_keeps_value(self):
        doc = self._get_page("/my/orders?search=WSPREF&search_in=client_order_ref")
        inputs = doc.xpath("//form[contains(@class, 'o_portal_search_panel')]//input[@name='search']")
        self.assertTrue(inputs)
        self.assertEqual(inputs[0].get("value"), "WSPREF")
