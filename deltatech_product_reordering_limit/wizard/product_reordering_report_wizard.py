import base64
import io

import xlsxwriter

from odoo import fields, models
from odoo.exceptions import UserError


class ProductReorderingReportWizard(models.TransientModel):
    _name = "product.reordering.report.wizard"
    _description = "Product Reordering Report Wizard"

    file = fields.Binary("File", readonly=True)
    filename = fields.Char("Filename", readonly=True)

    def _get_products(self):
        """Return the product templates selected when the wizard was opened.

        Contextul poate lipsi (acțiune apelată direct) sau poate proveni de la alt
        model, caz în care active_ids sunt id-uri străine de product.template.
        """
        if self.env.context.get("active_model") != "product.template":
            return self.env["product.template"]
        return self.env["product.template"].browse(self.env.context.get("active_ids") or [])

    def action_generate_report(self):
        products = self._get_products()
        if not products:
            raise UserError(self.env._("Select at least one product to generate the reordering report."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Reordering Report")
        bold = workbook.add_format({"bold": True})
        red_format = workbook.add_format({"font_color": "red"})
        green_format = workbook.add_format({"font_color": "green"})

        headers = ["Default Code", "Name", "Under Quantity", "Required Quantity", "Range"]
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        row = 1
        for product in products:
            available = product.qty_available
            min_total = product.total_minimum
            max_total = product.total_maximum

            under_qty = max(0.0, min_total - available)
            required_qty = max(0.0, max_total - available)
            reorder_range = f"{min_total} -> {max_total}"

            sheet.write(row, 0, product.default_code or "")
            sheet.write(row, 1, product.display_name or "")
            sheet.write(row, 2, under_qty, red_format if under_qty > 0 else None)
            sheet.write(row, 3, required_qty, green_format if required_qty > 0 else None)
            sheet.write(row, 4, reorder_range)
            row += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        self.write({"file": file_data, "filename": "Reordering_Report.xlsx"})

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
