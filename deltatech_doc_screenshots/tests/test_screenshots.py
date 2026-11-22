# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Capturile fișei consultant a uneltei: același ecran în RO (fișa) și în EN (USAGE.md)."""

from odoo.tests import tagged

from .screenshot_case import ScreenshotCase


@tagged("-at_install", "post_install", "fise_screenshots")
class TestDocScreenshotsScreenshots(ScreenshotCase):
    screenshots_module = "deltatech_doc_screenshots"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.prepare_ro_company()

    @staticmethod
    def _demo_xlsx(lang):
        """Un export XLSX mic, cu sume în formatul ``#,##0.00``, pentru captura din Pasul 4."""
        import io  # noqa: PLC0415

        from openpyxl import Workbook  # noqa: PLC0415

        ro = lang == "ro_RO"
        wb = Workbook()
        ws = wb.active
        ws.append(["Partener", "Facturat", "Încasat", "Sold"] if ro else ["Partner", "Invoiced", "Paid", "Balance"])
        for name, invoiced, paid in (
            ("Ferma Verde SRL", 12345.6, 10000.0),
            ("Agro Prod SRL", 2780.25, 2780.25),
            ("Gemini Furniture", 1234567.89, 1000000.0),
        ):
            ws.append([name, invoiced, paid, round(invoiced - paid, 2)])
        for row in ws.iter_rows(min_row=2, min_col=2):
            for cell in row:
                cell.number_format = "#,##0.00"
        ws.column_dimensions["A"].width = 22
        for col in "BCD":
            ws.column_dimensions[col].width = 14
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def _shots(self, lang="ro_RO"):
        action = self.env.ref("base.action_res_company_form")
        title = "Solduri parteneri" if lang == "ro_RO" else "Partner balances"
        return [
            # formularul companiei demo, cu câmpurile evidențiate ①②
            {
                "url": f"action={action.id}&id={self.company.id}&model=res.company&view_type=form",
                "name": "01_formular_companie.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='name']", "div[name='vat']"],
                "settle": 2000,
            },
            # un export XLSX transformat în imagine (Pasul 4)
            self.xlsx_shot(self._demo_xlsx(lang), "02_export_xlsx.png", title=title, lang=lang),
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots("en_US"), hide_systray=True, lang="en_US")

    def _gif_steps(self):
        action = self.env.ref("base.action_partner_form")
        return [
            {"goto": f"action={action.id}&model=res.partner&view_type=form", "wait": ".o_form_view"},
            {
                "caption": {
                    "ro_RO": "Un partener nou începe cu denumirea",
                    "en_US": "A new partner starts with the name",
                }
            },
            {"type": "Ferma Verde SRL", "into": "name", "hold": 500},
            {"caption": {"ro_RO": "Apoi codul fiscal", "en_US": "Then the tax ID"}},
            {"type": "RO99999143", "into": "vat", "hold": 500},
            {
                "caption": {
                    "ro_RO": "La salvare, partenerul e gata de lucru",
                    "en_US": "Once saved, the partner is ready",
                }
            },
            {"click": ".o_form_button_save", "wait_after": ".o_form_saved", "hold": 2200},
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        """GIF-ul demo al uneltei (pilot pentru ``capture_gif``), în RO și EN."""
        # banner.json e în engleză: slide-ul RO primește textele lui
        intro_ro = {
            "title": "Capturi pentru documentație",
            "summary": "Capturile și demo-urile fișei generate din teste",
            "features": ["Capturi generate din teste", "Pași evidențiați", "GIF-uri demo"],
        }
        self.capture_gif(self._gif_steps(), name="demo.gif", intro=intro_ro)
        self.capture_gif(self._gif_steps(), name="demo.gif", lang="en_US")
