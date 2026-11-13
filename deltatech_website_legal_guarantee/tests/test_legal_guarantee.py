# © 2026 Deltatech
# See README.rst file on addons root folder for license details
from lxml import html

from odoo.tests import HttpCase, tagged

from ..models.website import NOTICE_LANGS, YOUREUROPE_PATHS

IMG_PATH = "/deltatech_website_legal_guarantee/static/src/img/notice/"


@tagged("post_install", "-at_install")
class TestLegalGuarantee(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("base.default_website")
        cls.product = cls.env["product.template"].create(
            {
                "name": "Legal guarantee test product",
                "type": "consu",
                "list_price": 100.0,
                "sale_ok": True,
                "website_published": True,
            }
        )

    def _get_page(self, url):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        return html.fromstring(response.content)

    def test_page_shows_official_notice(self):
        page = self._get_page("/garantie")
        images = page.xpath("//div[@id='wrap']//figure[contains(@class, 'o_legal_guarantee_notice')]//img")
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].get("src"), IMG_PATH + "legal_guarantee_notice_en.svg")
        hrefs = page.xpath("//div[@id='wrap']//figure[contains(@class, 'o_legal_guarantee_notice')]//a/@href")
        self.assertIn("https://europa.eu/youreurope/guarantees", hrefs)
        self.assertIn(IMG_PATH + "legal_guarantee_notice_en.pdf", hrefs)
        for url in (images[0].get("src"), IMG_PATH + "legal_guarantee_notice_en.pdf"):
            self.assertEqual(self.url_open(url).status_code, 200)

    def test_notice_in_romanian(self):
        self.env["res.lang"]._activate_lang("ro_RO")
        notice = self.website.with_context(lang="ro_RO")._get_legal_guarantee_notice()
        self.assertEqual(notice["image_url"], IMG_PATH + "legal_guarantee_notice_ro.png")
        self.assertEqual(notice["pdf_url"], IMG_PATH + "legal_guarantee_notice_ro.pdf")
        self.assertEqual(notice["link_text"], "europa.eu/youreurope/garanții")
        self.assertEqual(notice["link_url"], "https://europa.eu/youreurope/garan%C8%9Bii")
        self.assertEqual(self.url_open(notice["image_url"]).status_code, 200)

    def test_footer_link(self):
        xpath = "//footer//div[contains(@class, 'o_footer_legal_guarantee')]//a/@href"
        hrefs = self._get_page("/").xpath(xpath)
        self.assertEqual(len(hrefs), 1)
        self.assertTrue(hrefs[0].endswith("/garantie"))
        self.website.legal_guarantee_footer = False
        self.assertFalse(self._get_page("/").xpath(xpath))

    def test_product_page_link_and_modal(self):
        page = self._get_page(self.product.website_url)
        links = page.xpath("//a[contains(@class, 'o_legal_guarantee_link')]")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].get("data-bs-target"), "#o_legal_guarantee_modal")
        self.assertEqual(len(page.xpath("/html/body/div[@id='o_legal_guarantee_modal']//img")), 1)
        self.website.legal_guarantee_product = False
        page = self._get_page(self.product.website_url)
        self.assertFalse(page.xpath("//a[contains(@class, 'o_legal_guarantee_link')]"))

    def test_every_eu_language_has_notice_files(self):
        self.assertEqual(len(NOTICE_LANGS), 24)
        self.assertEqual(set(NOTICE_LANGS), set(YOUREUROPE_PATHS))
        for code in NOTICE_LANGS:
            lang = self.env["res.lang"].with_context(active_test=False).search([("code", "like", code + "_%")], limit=1)
            if not lang:
                continue
            lang.active = True
            notice = self.website.with_context(lang=lang.code)._get_legal_guarantee_notice()
            self.assertIn("legal_guarantee_notice_" + code + ".", notice["image_url"])
            for url in (notice["image_url"], notice["pdf_url"]):
                self.assertEqual(self.url_open(url).status_code, 200, url)

    def test_other_language_falls_back_to_english(self):
        self.env["res.lang"]._activate_lang("ja_JP")
        notice = self.website.with_context(lang="ja_JP")._get_legal_guarantee_notice()
        self.assertEqual(notice["image_url"], IMG_PATH + "legal_guarantee_notice_en.svg")

    def test_national_block_follows_company_country(self):
        xpath = "//div[@id='wrap']//h3[contains(text(), 'National rules in Romania')]"
        self.website.company_id.country_id = self.env.ref("base.ro")
        self.assertEqual(len(self._get_page("/garantie").xpath(xpath)), 1)
        self.website.company_id.country_id = self.env.ref("base.de")
        self.assertFalse(self._get_page("/garantie").xpath(xpath))

    def test_seller_address_without_company_name(self):
        company = self.website.company_id
        company.write({"name": "Seller Test SRL", "street": "Main St 1", "city": "Bucharest"})
        text = " ".join(
            self._get_page("/garantie").xpath("//div[contains(@class, 'o_legal_guarantee_seller')]")[0].itertext()
        )
        self.assertEqual(text.count("Seller Test SRL"), 1)
        self.assertIn("Main St 1", text)
