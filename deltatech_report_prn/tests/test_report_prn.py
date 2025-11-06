# © 2008-2025 Deltatech / Terrabit
# See README.rst for license details

from urllib.parse import quote

from odoo.tests.common import HttpCase, TransactionCase, tagged

QWEB_ARCH = '<t t-name="deltatech_report_prn.test_prn_tmpl">Hello PRN: <t t-esc="docs and docs[0].name or \'\'"/></t>'


@tagged("post_install", "-at_install")
class TestPrnRender(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a minimal QWeb template and register it with an xml_id
        self.view = self.env["ir.ui.view"].create(
            {
                "name": "Test PRN Template",
                "type": "qweb",
                "key": "deltatech_report_prn.test_prn_tmpl",
                "arch_db": QWEB_ARCH,
            }
        )
        # Create a report action using our template
        self.report_action = self.env["ir.actions.report"].create(
            {
                "name": "Test PRN Report",
                "model": "res.partner",
                "report_name": "deltatech_report_prn.test_prn_tmpl",
                "report_type": "qweb-prn",
                "print_report_name": "'PRN-' + (object.name or 'noname')",
            }
        )
        # Sample record
        self.partner = self.env["res.partner"].create({"name": "Alpha"})

    def test_render_qweb_prn(self):
        # Call the specific renderer
        content, out_type = self.env["ir.actions.report"]._render_qweb_prn(
            self.report_action.report_name, [self.partner.id], data={}
        )
        self.assertEqual(out_type, "text")
        self.assertIsInstance(content, (bytes, bytearray))
        self.assertIn(b"Hello PRN", content)
        self.assertIn(b"Alpha", content)

    def test_generic_render_dispatch(self):
        # Ensure the generic dispatcher also resolves qweb-prn
        content, out_type = self.env["ir.actions.report"]._render(self.report_action.report_name, [self.partner.id])
        self.assertEqual(out_type, "text")
        self.assertIn(b"Alpha", content)


@tagged("post_install", "-at_install")
class TestPrnHttp(HttpCase):
    def setUp(self):
        super().setUp()
        # Create a dedicated test user to avoid admin MFA/password issues
        Users = self.env["res.users"].with_context(no_reset_password=True)
        group_user = self.env.ref("base.group_user")
        Users.create(
            {
                "name": "PRN Test User",
                "login": "prn_test",
                "password": "test",
                "email": "prn_test@example.com",
                "group_ids": [(6, 0, [group_user.id])],
            }
        )

        # Authenticate as the test user to access protected report routes
        self.authenticate("prn_test", "test")
        # Setup similar to TransactionCase
        self.view = self.env["ir.ui.view"].create(
            {
                "name": "Test PRN Template",
                "type": "qweb",
                "key": "deltatech_report_prn.test_prn_tmpl",
                "arch_db": QWEB_ARCH,
            }
        )
        self.report_action = self.env["ir.actions.report"].create(
            {
                "name": "Test PRN Report",
                "model": "res.partner",
                "report_name": "deltatech_report_prn.test_prn_tmpl",
                "report_type": "qweb-prn",
                "print_report_name": "'PRN-' + (object.name or 'noname')",
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Beta"})

    def test_route_prn_direct(self):
        # Direct route using /report/prn/<reportname>/<docids>
        reportname = quote(self.report_action.report_name, safe="")
        url = f"/report/prn/{reportname}/{self.partner.id}"
        resp = self.url_open(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("Content-Type"), "text/plain")
        self.assertIn(b"Hello PRN", resp.content)
        self.assertIn(b"Beta", resp.content)
