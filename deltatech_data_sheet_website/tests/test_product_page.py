# © 2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Linkurile spre fișa tehnică și fișa de securitate pe pagina produsului din magazin (#3381):
# secțiunea Documente apare și fără documente standard, iar PDF-ul se descarcă fără autentificare.
import base64

from lxml import html

from odoo.tests import HttpCase, tagged

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@tagged("-at_install", "post_install")
class TestDataSheetProductPage(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data_sheet = cls._attachment("data_sheet.pdf")
        cls.safety_sheet = cls._attachment("safety_sheet.pdf")

    @classmethod
    def _attachment(cls, name):
        return cls.env["ir.attachment"].create(
            {"name": name, "datas": base64.b64encode(PDF), "mimetype": "application/pdf", "public": True}
        )

    def _product(self, **vals):
        return self.env["product.template"].create(
            dict({"name": "Data sheet product", "sale_ok": True, "website_published": True}, **vals)
        )

    def _documents(self, product):
        """Linkurile din secțiunea Documente, sau None dacă secțiunea lipsește."""
        response = self.url_open(f"/shop/{product.id}")
        self.assertEqual(response.status_code, 200)
        block = html.fromstring(response.content).xpath("//div[@id='product_documents']")
        if not block:
            return None
        return [a.get("href") for a in block[0].xpath(".//a")]

    def _href(self, attachment):
        return f"/web/content/{attachment.id}?download=true"

    def test_data_sheet_only(self):
        product = self._product(data_sheet_id=self.data_sheet.id)
        self.assertEqual(self._documents(product), [self._href(self.data_sheet)])

    def test_safety_sheet_only(self):
        product = self._product(safety_data_sheet_id=self.safety_sheet.id)
        self.assertEqual(self._documents(product), [self._href(self.safety_sheet)])

    def test_both_sheets(self):
        product = self._product(data_sheet_id=self.data_sheet.id, safety_data_sheet_id=self.safety_sheet.id)
        self.assertEqual(self._documents(product), [self._href(self.data_sheet), self._href(self.safety_sheet)])

    def test_no_sheet_no_section(self):
        product = self._product()
        self.assertIsNone(self._documents(product))

    def test_sheet_after_standard_document(self):
        product = self._product(data_sheet_id=self.data_sheet.id)
        document = self.env["product.document"].create(
            {
                "ir_attachment_id": self._attachment("manual.pdf").id,
                "res_model": "product.template",
                "res_id": product.id,
                "shown_on_product_page": True,
            }
        )
        links = self._documents(product)
        self.assertEqual(len(links), 2)
        self.assertTrue(links[0].endswith(f"/document/{document.id}"))
        self.assertEqual(links[1], self._href(self.data_sheet))

    def test_anonymous_download(self):
        response = self.url_open(self._href(self.data_sheet))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertEqual(response.content, PDF)
