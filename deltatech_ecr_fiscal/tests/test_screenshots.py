# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturile fișei consultant: câmpurile rezultatului de pe casa de marcat, pe factură.
# Modulul nu are ecrane proprii: câmpurile se văd în fișierul dat de Export pe facturi (un bon
# real, unul simulat și unul refuzat de casă).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_ecr_fiscal,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_ecr_fiscal:TestEcrFiscalScreenshots --stop-after-init
import io
import unittest

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

FIELDS = (
    "name",
    "fiscal_state",
    "fiscal_receipt_number",
    "fiscal_doc_number",
    "fiscal_z",
    "fiscal_simulated",
)


@tagged("-at_install", "post_install", "fise_screenshots")
class TestEcrFiscalScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_ecr_fiscal"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Magazin SRL")
        partner = cls.env["res.partner"].create({"name": "Client magazin"})
        values = (
            # bon real: NR unic pe aparat, BF din raportul Z 14
            {"fiscal_state": "done", "fiscal_receipt_number": "7", "fiscal_doc_number": "1287", "fiscal_z": "14"},
            # bon de pe casa simulată: are numere, dar nu e document fiscal
            {
                "fiscal_state": "done",
                "fiscal_receipt_number": "1",
                "fiscal_doc_number": "1",
                "fiscal_z": "1",
                "fiscal_simulated": True,
            },
            # casa a refuzat bonul
            {"fiscal_state": "error", "fiscal_error": "Lipsă hârtie"},
        )
        cls.invoices = cls.env["account.move"]
        for index, vals in enumerate(values):
            invoice = cls._create_invoice_one_line(partner_id=partner.id, price_unit=100.0 + index * 10, post=True)
            invoice.write(vals)
            cls.invoices |= invoice

    def _export_xlsx(self, lang):
        """Fișierul pe care îl dă **Export** cu câmpurile fiscale, ca XLSX."""
        import xlsxwriter

        invoices = self.invoices.with_context(lang=lang)
        model_fields = invoices._fields
        headers = [model_fields[f].get_description(invoices.env)["string"] for f in FIELDS]
        rows = invoices.export_data(list(FIELDS)).get("datas", [])
        buffer = io.BytesIO()
        book = xlsxwriter.Workbook(buffer, {"in_memory": True})
        sheet = book.add_worksheet()
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        bold = book.add_format({"bold": True, "bg_color": "#E9ECEF", "border": 1})
        cell = book.add_format({"border": 1})
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)
            sheet.set_column(col, col, 20)
        for row_index, row in enumerate(rows, start=1):
            for col, value in enumerate(row):
                sheet.write(row_index, col, value if value not in (None, False) else "", cell)
        book.close()
        return buffer.getvalue()

    def _shots(self, lang="ro_RO"):
        title = {"ro_RO": "Export facturi: câmpurile casei de marcat", "en_US": "Invoice export: cash register fields"}
        return [self.xlsx_shot(self._export_xlsx(lang), "01_export_facturi.png", title=title[lang])]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots("en_US"), hide_systray=True, lang="en_US")
