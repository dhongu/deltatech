# ©  2025 Terrabit
# See README.rst file on addons root folder for license details

import importlib.util
import json
from pathlib import Path

from lxml import etree

from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import SQL


@tagged("post_install", "-at_install")
class TestConfigDetails(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login="cfg_sales", groups="sales_team.group_sale_salesman")
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
        cls.product = cls.env["product.product"].create({"name": "Window"})

    def line(self, details):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "name": "Window", "config_details": details}),
                ],
            }
        )
        return order.order_line

    def test_json_roundtrip_and_html(self):
        """CA1, CA2: stored as JSON; the HTML shows texts and nested groups, never the ``id`` key."""
        details = [
            {"name": "Identitate", "value": {"id": "SECRET-ID", "pozitie": "1"}},
            {"name": "Parti", "value": {"Usa": {"x": "900", "y": "2100"}}},
            {"name": "Amplasare", "value": "Dormitor"},
        ]
        line = self.line(details)
        self.assertEqual(line.config_details, details)
        html = str(line.get_html_config_details(with_attributes=True))
        for expected in ("pozitie: 1", "Usa", "x: 900", "Amplasare:", "Dormitor"):
            self.assertIn(expected, html)
        self.assertNotIn("SECRET-ID", html)
        self.assertNotIn("Dormitor", str(line.get_html_config_details()))  # plain text only with attributes

    def test_no_eval_and_escaping(self):
        """CA3, CA4: text is escaped and never evaluated; malformed values give an empty list."""
        line = self.line([{"name": "<b>n</b>", "value": {"k": "<script>alert(1)</script>"}}])
        html = str(line.get_html_config_details())
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertEqual(self.line(False)._get_config_details(), [])
        self.assertEqual(self.line("not json at all")._get_config_details(), [])
        self.assertEqual(self.line(42)._get_config_details(), [])
        self.assertEqual(str(self.line(False).get_html_config_details()), "")
        # a text that would run code is not evaluated
        self.assertEqual(self.line("__import__('os').getcwd()")._get_config_details(), [])

    def test_images(self):
        """CA5: pictures with an "Open image" link; the image URLs are returned."""
        line = self.line([{"name": "Img", "value": {"image": "/web/image/1", "src": "/web/image/2", "x": "1"}}])
        self.assertEqual(line.get_images_config_detail(), ["/web/image/1"])
        html = str(line.get_html_config_details())
        self.assertIn("<img src='/web/image/1' width='100'", html)
        self.assertIn("<img src='/web/image/2' width='200'", html)
        self.assertIn("Open image", html)

    def test_open_details(self):
        """CA6: the Details button opens a read-only form for a salesman."""
        line = self.line([{"name": "Dim", "value": {"x": "10"}}]).with_user(self.user)
        action = line.action_open_config_details()
        self.assertEqual(action["res_model"], "sale.order.line.config.details")
        self.assertEqual(action["target"], "new")
        wizard = self.env["sale.order.line.config.details"].with_user(self.user).browse(action["res_id"])
        self.assertIn("x: 10", wizard.config_details)

    def test_order_form_list_columns(self):
        """CA7: the Details button is its own column: the quantity column keeps its header and its fields."""
        arch = self.env["sale.order"].get_view(self.env.ref("sale.view_order_form").id)["arch"]
        root = etree.fromstring(arch)
        sol_qty = root.xpath("//field[@name='order_line']//list//column[@name='sol_qty']")[0]
        self.assertTrue(sol_qty.xpath(".//field[@name='product_uom_qty']"))
        self.assertFalse(sol_qty.xpath(".//button[@name='action_open_config_details']"))
        self.assertFalse(sol_qty.xpath(".//field[@name='config_details']"))
        button = root.xpath("//field[@name='order_line']//list/button[@name='action_open_config_details']")
        self.assertEqual(len(button), 1)
        self.assertEqual(button[0].get("invisible"), "not config_details")

    def test_legacy_formats(self):
        """CA8: JSON text, str() of a Python list, bare dictionaries and numbers are shown."""
        details = [{"name": "Dim", "value": {"x": "900"}}]
        self.assertEqual(self.line(json.dumps(details))._get_config_details(), details)
        self.assertEqual(self.line(str(details))._get_config_details(), details)
        line = self.line([{"Latime": 900, "Inaltime": "2100", "id": "X"}])
        html = str(line.get_html_config_details())
        self.assertIn("Latime: 900", html)
        self.assertIn("Inaltime: 2100", html)
        self.assertNotIn(">X<", html)
        self.assertEqual(self.line({"name": "Dim", "value": {"x": "1"}})._get_config_details()[0]["name"], "Dim")
        # a group without a name shows its values without a "None:" label
        html = str(self.line([{"value": {"x": "7"}}]).get_html_config_details())
        self.assertIn("x: 7", html)
        self.assertNotIn("None", html)

    def test_copy(self):
        """CA10: duplicating the order copies the details."""
        details = [{"name": "Dim", "value": {"x": "900"}}]
        order = self.line(details).order_id
        self.assertEqual(order.copy().order_line.config_details, details)

    def _migrate(self):
        path = Path(__file__).parents[1] / "migrations" / "20.0.1.1.0" / "pre-migration.py"
        spec = importlib.util.spec_from_file_location("config_details_pre_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "19.0.0.0.0")

    def _column_type(self):
        self.env.cr.execute(
            SQL(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'sale_order_line' AND column_name = 'config_details'"
            )
        )
        return self.env.cr.fetchone()[0]

    def test_migration_from_text(self):
        """CA9: a 19.0 text column is converted to JSON, line by line, nothing lost."""
        details = [{"name": "Dim", "value": {"x": "900"}}]
        lines = self.line(False) | self.line(False) | self.line(False) | self.line(False)
        self.env.flush_all()
        cr = self.env.cr
        cr.execute(SQL("ALTER TABLE sale_order_line ALTER COLUMN config_details TYPE text USING NULL"))
        for line, text in zip(lines, [json.dumps(details), str(details), "plain text", None], strict=True):
            cr.execute(SQL("UPDATE sale_order_line SET config_details = %s WHERE id = %s", text, line.id))
        self._migrate()
        self.assertEqual(self._column_type(), "jsonb")
        self.env.invalidate_all()
        self.assertEqual(lines[0].config_details, details)
        self.assertEqual(lines[1].config_details, details)
        self.assertEqual(lines[2].config_details, "plain text")
        self.assertFalse(lines[3].config_details)

    def test_migration_already_json(self):
        """CA9: a database already on 20.0 (jsonb column) is left as it is."""
        details = [{"name": "Dim", "value": {"x": "900"}}]
        line = self.line(details)
        self.env.flush_all()
        self._migrate()
        self.assertEqual(self._column_type(), "jsonb")
        self.env.invalidate_all()
        self.assertEqual(line.config_details, details)
