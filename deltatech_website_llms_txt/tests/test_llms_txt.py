# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestLlmsTxt(HttpCase):
    def setUp(self):
        super().setUp()
        self.website = self.env["website"].get_current_website()
        self.site_url = self.website.get_base_url()
        self.website.company_id.write({"email": "shop@example.com", "phone": "+40 700 000 000"})
        view = self.env["ir.ui.view"].create({"name": "LLMS page", "type": "qweb", "arch": "<t><div>LLMS</div></t>"})
        self.page = self.env["website.page"].create(
            {
                "name": "LLMS Delivery",
                "url": "/llms-delivery",
                "view_id": view.id,
                "website_id": self.website.id,
                "is_published": True,
                "website_meta_description": "How we deliver [fast]",
            }
        )
        view_hidden = self.env["ir.ui.view"].create(
            {"name": "LLMS draft", "type": "qweb", "arch": "<t><div>LLMS</div></t>"}
        )
        self.draft = self.env["website.page"].create(
            {
                "name": "LLMS Draft",
                "url": "/llms-draft",
                "view_id": view_hidden.id,
                "website_id": self.website.id,
                "is_published": False,
            }
        )

    def test_generated(self):
        self.website.llms_txt_summary = "We sell   tools\nfor gardens."
        self.website.llms_txt_details = "## Delivery\n\nAll of Romania in 48h."
        content = self.website._get_llms_txt()
        lines = content.splitlines()
        self.assertEqual(lines[0], f"# {self.website.name}")
        self.assertIn("> We sell tools for gardens.", lines)
        self.assertIn("Contact: shop@example.com · +40 700 000 000", content)
        self.assertIn("All of Romania in 48h.", content)
        self.assertIn(f"- [LLMS Delivery]({self.site_url}/llms-delivery): How we deliver [fast]", lines)
        self.assertNotIn("/llms-draft", content)
        self.assertIn(f"- [Sitemap]({self.site_url}/sitemap.xml)", lines)
        self.assertTrue(content.endswith("\n"))

    def test_unindexed_page_left_out(self):
        self.page.website_indexed = False
        self.assertNotIn("/llms-delivery", self.website._get_llms_txt())

    def test_link_text_brackets(self):
        self.page.name = "LLMS [New] page"
        self.assertIn("- [LLMS (New) page](", self.website._get_llms_txt())

    def test_custom_file(self):
        self.website.llms_txt_custom = "# Custom\n\n> Written by hand\n"
        self.assertEqual(self.website._get_llms_txt(), "# Custom\n\n> Written by hand\n")

    def test_route(self):
        resp = self.url_open("/llms.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers["Content-Type"].startswith("text/plain"))
        self.assertTrue(resp.text.startswith(f"# {self.website.name}"))

    def test_route_disabled(self):
        self.website.llms_txt_enabled = False
        self.assertEqual(self.url_open("/llms.txt").status_code, 404)
