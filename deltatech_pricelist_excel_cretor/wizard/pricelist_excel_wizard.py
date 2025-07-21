import io

import xlsxwriter

from odoo import _, fields, models
from odoo.exceptions import UserError


class PricelistExcelWizard(models.TransientModel):
    _name = "pricelist.excel.wizard"
    _description = "Pricelist Excel Wizard"

    price_list_id = fields.Many2one("product.pricelist", string="Price List", required=True)
    partner_id = fields.Many2one("res.partner", string="Partner")
    # file_data = fields.Binary("File", readonly=True)
    # file_name = fields.Char("File Name", readonly=True)

    def do_compute(self):
        if not self.price_list_id:
            raise UserError(_("Please select a Price List."))

        # Fetch all products
        products = self.env["product.product"].search([])

        # Create an in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Products")
        decimal_format = workbook.add_format({"num_format": "0.00"})

        # Write headers
        headers = ["Product Name", "Default Code", "Sale Price"]
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        # Write product data
        row = 1
        for product in products:
            price = self.price_list_id._get_product_price(
                product, 1, currency=self.price_list_id.currency_id, partner=self.partner_id
            )
            sheet.write(row, 0, product.with_context(display_default_code=False).display_name)
            sheet.write(row, 1, product.default_code or "")
            sheet.write(row, 2, price, decimal_format)
            row += 1

        # Close workbook and reset the stream
        workbook.close()
        output.seek(0)

        # Create an attachment with the file data
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Pricelist_Products.xlsx",
                "type": "binary",
                "raw": output.read(),
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )
        output.close()

        # Return action to download the file
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}",
            "target": "new",
        }
