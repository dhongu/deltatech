import base64
from io import BytesIO

import xlsxwriter

from odoo import fields, models


class ExportPurchaseLine(models.TransientModel):
    _name = "export.purchase.line"
    _description = "Export Purchase Lines"

    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")
    data_file = fields.Binary(string="File", readonly=True)
    name = fields.Char(string="File Name", readonly=True, default="purchase_order.xlsx")

    def do_export(self):
        active_ids = self.env.context.get("active_ids", [])
        active_model = self.env.context.get("active_model", "sale.order")
        orders = self.env[active_model].browse(active_ids)
        output_buffer = BytesIO()
        workbook = xlsxwriter.Workbook(output_buffer)
        worksheet = workbook.add_worksheet("Order Lines")
        worksheet.write(0, 0, "Code")
        worksheet.write(0, 1, "Internal Code")
        worksheet.write(0, 2, "Name")
        worksheet.write(0, 3, "Qty")
        worksheet.write(0, 4, "Price")
        worksheet.write(0, 5, "Unit of Measure")
        lin = 1
        for order in orders:
            for line in order.order_line:
                product = line.product_id.with_context(partner_id=order.partner_id.id)
                code = ""
                name = product.name
                if product.seller_ids:
                    product_sellers = product.seller_ids.filtered(
                        lambda s, partner_id=order.partner_id: s.partner_id == partner_id
                    )
                    if product_sellers:
                        product_seller = product_sellers[0]
                        if product_seller.product_code:
                            code = product_seller.product_code
                        if product_seller.product_name:
                            name = product_seller.product_name
                worksheet.write(lin, 0, code or "")
                worksheet.write(lin, 1, product.default_code or "")
                worksheet.write(lin, 2, name or "")
                worksheet.write(lin, 3, line.product_qty)
                worksheet.write(lin, 4, line.price_unit)
                worksheet.write(lin, 5, line.product_uom.name)
                lin += 1

        workbook.close()

        # Set the data_file field with the content of the file
        self.write(
            {
                "state": "get",
                "name": "purchase_order.xlsx",
                "data_file": base64.b64encode(output_buffer.getvalue()),
            }
        )
        output_buffer.close()

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }
