# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBaseUrl(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_url = "https://odoo.example.com"
        cls.env["ir.config_parameter"].sudo().set_param("web.base.url", cls.base_url)
        cls.env.company.website = "https://shop.example.com"

    def test_context_base_url(self):
        icp = self.env["ir.config_parameter"].sudo()
        self.assertEqual(
            icp.with_context(web_base_url="https://shop.example.com").get_param("web.base.url"),
            "https://shop.example.com",
        )

    def test_context_base_url_not_cached(self):
        # a call with the website in the context must not change the value
        # returned to the calls made afterwards without it
        icp = self.env["ir.config_parameter"].sudo()
        icp.with_context(web_base_url="https://shop.example.com").get_param("web.base.url")
        self.assertEqual(icp.get_param("web.base.url"), self.base_url)
        self.assertEqual(self.env.company.partner_id.get_base_url(), self.base_url)

    def test_template_keeps_base_url(self):
        # e-mails of other templates keep web.base.url, even when the record
        # company has a website
        partner = self.env["res.partner"].create(
            {"name": "Feedback customer", "email": "customer@example.com", "company_id": self.env.company.id}
        )
        template = self.env["mail.template"].create(
            {
                "name": "Base url test",
                "model_id": self.env["ir.model"]._get_id("res.partner"),
                "subject": "Test",
                "email_to": "{{ object.email }}",
                "body_html": '<p><t t-out="object.get_base_url()"/></p>',
            }
        )
        mail = self.env["mail.mail"].browse(template.send_mail(partner.id))
        self.assertIn(self.base_url, mail.body_html)
        self.assertEqual(self.env["ir.config_parameter"].sudo().get_param("web.base.url"), self.base_url)
