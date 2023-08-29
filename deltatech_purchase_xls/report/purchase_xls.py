# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class PurchaseOrderXlsx(models.AbstractModel):
    _name = "report.report_xlsx.purchase_order_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "PurchaseOrderXlsx"

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet("Import")
        sheet.write(0, 0, "Code")
        sheet.write(0, 1, "Internal Code")
        sheet.write(0, 2, "Name")
        sheet.write(0, 3, "Qty")
        sheet.write(0, 4, "Price")
        lin = 1
        for order in objs:
            for line in order.order_line:
                product = line.product_id.with_context(partner_id=order.partner_id.id)
                code = ""
                name = product.name
                if product.seller_ids:
                    product_sellers = product.seller_ids.filtered(lambda s: s.name == order.partner_id)
                    if product_sellers:
                        product_seller = product_sellers[0]
                        if product_seller.product_code:
                            code = product_seller.product_code
                        if product_seller.product_name:
                            name = product_seller.product_name
                sheet.write(lin, 0, code or "")
                sheet.write(lin, 1, product.default_code or "")
                sheet.write(lin, 2, name or "")
                sheet.write(lin, 3, line.product_qty)
                sheet.write(lin, 4, line.price_unit)
                lin += 1
