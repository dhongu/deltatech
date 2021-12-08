# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


import base64
from io import BytesIO

from odoo import models
from odoo.tools.misc import xlsxwriter


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def get_counter_lines(self):

        consumptions = self.env["service.consumption"].search([("invoice_id", "in", self.ids)])

        readings = self.env["service.meter.reading"].search([("consumption_id", "in", consumptions.ids)])
        meters_ids = []  # all meters with readings
        for reading in readings:
            if reading.meter_id not in meters_ids:
                meters_ids += [reading.meter_id]
        lines = []
        for meter_id in meters_ids:
            line = {}
            line["date"] = "2000-01-01"
            min = 9999999999
            max = 0
            for reading in readings:
                if reading.meter_id == meter_id:
                    if reading.previous_counter_value < min:
                        min = reading.previous_counter_value
                    if reading.counter_value > max:
                        max = reading.counter_value
                        line["date"] = reading.date
                    line["equipment_id"] = reading.equipment_id.display_name
                    # line[reading.id] = reading
                    line["min"] = min
                    line["max"] = max
                    line["serial_id"] = reading.equipment_id.serial_id.name
                    line["meter_id"] = reading.meter_id.name
                    line["address_id"] = reading.address_id.display_name
            lines += [line]

        return sorted(lines, key=lambda k: k["address_id"])

    def generate_excel_meters_report(self):
        # filename = 'filename.xls'
        temp_file = BytesIO()
        workbook = xlsxwriter.Workbook(temp_file, {"in_memory": True})
        worksheet = workbook.add_sheet("Sheet 1")

        # write cells
        # style = xlwt.easyxf('font: bold True, name Arial;')
        style = workbook.add_format({"font: bold True, name Arial;"})
        worksheet.write(0, 0, "Factura: " + self.number + "/" + self.date_invoice, style)
        worksheet.write(1, 0, "Client: " + self.partner_id.name, style)
        worksheet.write(2, 0, "Contract: " + self.agreement_id.name + "/" + self.agreement_id.date_agreement, style)
        worksheet.write(3, 0, "Data", style)
        worksheet.write(3, 1, "Echipament", style)
        worksheet.write(3, 2, "Serie", style)
        worksheet.write(3, 3, "Contor", style)
        worksheet.write(3, 4, "Instalat la", style)
        worksheet.write(3, 5, "Valoare precedenta", style)
        worksheet.write(3, 6, "Valoare citire", style)
        worksheet.write(3, 7, "Diferenta", style)
        total_readings = 0
        lines = self.get_counter_lines()
        crt_row = 4
        for line in lines:
            date = line["date"]
            worksheet.write(crt_row, 0, date.strftime("%d/%m/%Y"))
            worksheet.write(crt_row, 1, line["equipment_id"])
            worksheet.write(crt_row, 2, line["serial_id"])
            worksheet.write(crt_row, 3, line["meter_id"])
            worksheet.write(crt_row, 4, line["address_id"])
            worksheet.write(crt_row, 5, "{:,.0f}".format(line["min"]))
            worksheet.write(crt_row, 6, "{:,.0f}".format(line["max"]))
            worksheet.write(crt_row, 7, "{:,.0f}".format(line["max"] - line["min"]))
            crt_row += 1
            total_readings += int(line["max"]) - int(line["min"])
        crt_row += 1
        worksheet.write(crt_row, 6, "Total: ", style)
        worksheet.write(crt_row, 7, "{:,.0f}".format(total_readings), style)

        workbook.close()
        record_id = self.env["wizard.excel.report"].create(
            {
                "excel_file": base64.b64encode(temp_file.getvalue()),
                "file_name": "export_contori_" + self.number + ".xls",
            },
        )

        return {
            "view_mode": "form",
            "res_id": record_id.id,
            "res_model": "wizard.excel.report",
            "view_type": "form",
            "type": "ir.actions.act_window",
            "target": "new",
        }
