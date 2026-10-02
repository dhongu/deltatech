# Copyright (C) 2026 Terrabit
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import io

from PIL import Image

from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes
from odoo.tools.image import image_data_uri


def _png(color):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color).save(buffer, format="PNG")
    return BinaryBytes(buffer.getvalue())


@tagged("post_install", "-at_install")
class TestTeamLogo(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company_logo = _png((255, 0, 0))
        cls.team_logo = _png((0, 0, 255))
        cls.company.logo = cls.company_logo
        cls.company_src = image_data_uri(cls.company_logo)
        cls.team_src = image_data_uri(cls.team_logo)

        cls.team_with_logo = cls.env["crm.team"].create({"name": "Brand B", "logo": cls.team_logo})
        cls.team_without_logo = cls.env["crm.team"].create({"name": "Brand A"})
        cls.partner = cls.env["res.partner"].create({"name": "Client Team Logo"})
        cls.product = cls.env["product.product"].create(
            {"name": "Produs Team Logo", "type": "consu", "is_storable": True, "list_price": 10}
        )

    def _create_order(self, team):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "team_id": team.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1})],
            }
        )

    def _render(self, report_ref, records):
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(report_ref, records.ids)
        return html.decode() if isinstance(html, bytes) else str(html)

    def test_team_logo_field(self):
        self.assertEqual(self.team_with_logo.logo.content, self.team_logo.content)
        self.assertFalse(self.team_without_logo.logo)

    def test_sale_order_team_logo(self):
        order = self._create_order(self.team_with_logo)
        html = self._render("sale.action_report_saleorder", order)
        self.assertIn(self.team_src, html)
        self.assertNotIn(self.company_src, html)

    def test_sale_order_company_logo_fallback(self):
        order = self._create_order(self.team_without_logo)
        html = self._render("sale.action_report_saleorder", order)
        self.assertIn(self.company_src, html)
        self.assertNotIn(self.team_src, html)

    def test_all_layouts(self):
        order = self._create_order(self.team_with_logo)
        layouts = self.env["report.layout"].search([])
        self.assertTrue(layouts)
        for layout in layouts:
            with self.subTest(layout=layout.view_id.key):
                self.company.external_report_layout_id = layout.view_id
                html = self._render("sale.action_report_saleorder", order)
                self.assertIn(self.team_src, html)
                self.assertNotIn(self.company_src, html)

    def test_team_logo_without_company_logo(self):
        self.company.logo = False
        order = self._create_order(self.team_with_logo)
        for layout in self.env["report.layout"].search([]):
            with self.subTest(layout=layout.view_id.key):
                self.company.external_report_layout_id = layout.view_id
                html = self._render("sale.action_report_saleorder", order)
                self.assertIn(self.team_src, html)

    def test_picking_team_and_delivery_report(self):
        order = self._create_order(self.team_with_logo)
        order.action_confirm()
        picking = order.picking_ids
        self.assertTrue(picking)
        self.assertEqual(picking.team_id, self.team_with_logo)
        html = self._render("stock.action_report_delivery", picking)
        self.assertIn(self.team_src, html)
        self.assertNotIn(self.company_src, html)

    def test_picking_without_sale(self):
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", self.company.id)], limit=1
        )
        picking = self.env["stock.picking"].create({"picking_type_id": picking_type.id, "partner_id": self.partner.id})
        self.assertFalse(picking.team_id)
        html = self._render("stock.action_report_delivery", picking)
        self.assertIn(self.company_src, html)

    def test_direct_layout_call_keeps_company_logo(self):
        # Rapoartele care apelează direct o variantă de layout, fără web.external_layout,
        # nu au report_logo: trebuie să rămână logo-ul firmei.
        arch = """<t t-name="deltatech_team_logo.test_direct_layout">
            <t t-call="web.html_container">
                <t t-call="web.external_layout_standard"><div class="page">x</div></t>
            </t>
        </t>"""
        view = self.env["ir.ui.view"].create(
            {
                "name": "test_direct_layout",
                "type": "qweb",
                "arch": arch,
                "key": "deltatech_team_logo.test_direct_layout",
            }
        )
        html = str(
            self.env["ir.qweb"]._render(
                view.id,
                {"company": self.company, "o": self.company, "report_type": "pdf", "res_company": self.company},
            )
        )
        self.assertIn(self.company_src, html)

    def test_invoice_team_logo(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "team_id": self.team_with_logo.id,
                "invoice_line_ids": [(0, 0, {"product_id": self.product.id, "quantity": 1, "price_unit": 10})],
            }
        )
        html = self._render("account.account_invoices", invoice)
        self.assertIn(self.team_src, html)
        self.assertNotIn(self.company_src, html)
