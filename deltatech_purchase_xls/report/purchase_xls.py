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
        sheet.write(0, 1, "Name")
        sheet.write(0, 2, "Qty")

        lin = 1
        for order in objs:
            for line in order.order_line:
                sheet.write(lin, 0, line.product_id.default_code or "")
                sheet.write(lin, 1, line.product_id.name or "")
                sheet.write(lin, 2, line.product_qty)
                lin += 1
