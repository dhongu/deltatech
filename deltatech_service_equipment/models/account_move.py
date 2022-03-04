# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


import base64
from io import BytesIO

from odoo import _, models
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
            value_min = 9999999999
            value_max = 0
            for reading in readings:
                if reading.meter_id == meter_id:
                    if reading.previous_counter_value < value_min:
                        value_min = reading.previous_counter_value
                    if reading.counter_value > value_max:
                        value_max = reading.counter_value
                        line["date"] = reading.date
                    line["equipment_id"] = reading.equipment_id.display_name
                    # line[reading.id] = reading
                    line["min"] = value_min
                    line["max"] = value_max
                    line["serial_id"] = reading.equipment_id.serial_id.name
                    line["meter_id"] = reading.meter_id.name
                    line["address_id"] = reading.address_id.display_name
            lines += [line]

        return sorted(lines, key=lambda k: k["address_id"] or "")

    def generate_excel_meters_report(self):
        # filename = 'filename.xls'
        temp_file = BytesIO()
        workbook = xlsxwriter.Workbook(temp_file, {"in_memory": True})
        worksheet = workbook.add_worksheet("Sheet 1")

        agreements = self.invoice_line_ids.mapped("agreement_id")
        list_agreements = []
        for agreement in agreements:
            list_agreements += [("%s / %s") % (agreement.name, agreement.date_agreement)]
        agreements_string = ", ".join(agreements.mapped("name"))
        # write cells
        # style = xlwt.easyxf('font: bold True, name Arial;')
        style = workbook.add_format({"bold": True, "font_name": "Arial"})

        # date_default_style = workbook.add_format({"num_format": "dd/mm/yy"})

        worksheet.write(0, 0, _("Invoice: %s / %s") % (self.name, self.invoice_date), style)
        worksheet.write(1, 0, _("Customer: %s") % self.partner_id.name, style)
        worksheet.write(2, 0, _("Agreement: %s ") % (agreements_string), style)

        worksheet.write(3, 0, _("Data"), style)
        worksheet.write(3, 1, _("Equipment"), style)
        worksheet.write(3, 2, _("Serial"), style)
        worksheet.write(3, 3, _("Meter"), style)
        worksheet.write(3, 4, _("Installed at"), style)
        worksheet.write(3, 5, _("Previous value"), style)
        worksheet.write(3, 6, _("Read value"), style)
        worksheet.write(3, 7, _("Difference"), style)
        total_readings = 0
        lines = self.get_counter_lines()
        crt_row = 4
        for line in lines:
            date = line["date"]
            try:
                worksheet.write(crt_row, 0, date.strftime("%d/%m/%Y"))
            except Exception:
                worksheet.write(crt_row, 0, date)
            worksheet.write(crt_row, 1, line["equipment_id"])
            worksheet.write(crt_row, 2, line["serial_id"])
            worksheet.write(crt_row, 3, line["meter_id"])
            worksheet.write(crt_row, 4, line["address_id"])
            worksheet.write(crt_row, 5, line["min"])  # "{:,.0f}".format(line["min"]))
            worksheet.write(crt_row, 6, line["max"])  # "{:,.0f}".format(line["max"]))
            worksheet.write(crt_row, 7, line["max"] - line["min"])  # "{:,.0f}".format(line["max"] - line["min"]))
            crt_row += 1
            total_readings += int(line["max"]) - int(line["min"])
        crt_row += 1
        worksheet.write(crt_row, 6, "Total: ", style)
        worksheet.write(crt_row, 7, total_readings, style)  # "{:,.0f}".format(total_readings), style)

        workbook.close()
        data_file = base64.b64encode(temp_file.getvalue())
        file_name = "export_contori_" + self.name + ".xls"
        wizard = self.env["wizard.download.file"].create({"data_file": data_file, "file_name": file_name})
        return wizard.do_download_file()
