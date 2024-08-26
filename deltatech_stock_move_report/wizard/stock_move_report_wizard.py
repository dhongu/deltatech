import base64
from datetime import datetime
from io import BytesIO

import xlsxwriter

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockMoveReport(models.TransientModel):
    _name = "stock.move.report.wizard"

    starting_report_date = fields.Date("From", required=True)
    ending_report_date = fields.Date("To", required=True)
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")
    data_file = fields.Binary(string="File", readonly=True)
    name = fields.Char(string="File Name", readonly=True)
    def do_export(self):


        if self.starting_report_date > self.ending_report_date:
            raise UserError(_("Please make sure the second date is after the first"))
        picking=self.env['stock.picking'].search([('date_done','>=',self.starting_report_date),('date_done','<=',self.ending_report_date),('picking_type_id.code','=','outgoing'),('state','=','done')])
        headers = [_("Location"), _("Product"), _("Date"), _("Quantity Delivered")]
        matrix = [headers]
        for pick in picking:
            for line in pick.move_ids_without_package:
                matrix.append([pick.location_id.display_name,line.product_id.display_name,datetime.strftime(pick.date_done, "%Y-%m-%d"),line.product_uom_qty])

        output_buffer = BytesIO()
        workbook = xlsxwriter.Workbook(output_buffer)
        worksheet = workbook.add_worksheet("Stock Move Report")

        # Write the matrix data to the worksheet
        for row_idx, row in enumerate(matrix):
            for col_idx, cell in enumerate(row):
                worksheet.write(row_idx, col_idx, cell)

        # Close the workbook
        workbook.close()

        # Set the data_file field with the content of the file
        self.write(
            {"state": "get", "name": "stock_move_history_export.xlsx", "data_file": base64.b64encode(output_buffer.getvalue())}
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
