# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

import time

from odoo import api, fields, models


class ReportDCPrint(models.AbstractModel):
    _name = "report.deltatech_dc.report_dc"
    _description = "ReportDCPrint"
    _template = "deltatech_dc.report_dc"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(self._template)
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "time": time,
            "docs": self.env[report.model].browse(docids),
            "lot": False,
        }


class ReportDCLotPrint(models.AbstractModel):
    _name = "report.deltatech_dc.report_dc_lot"
    _description = "ReportDCPrint"
    _template = "deltatech_dc.report_dc_lot"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(self._template)
        lots = self.env[report.model].browse(docids)
        declarations = self.env["deltatech.dc"]
        for lot in lots:
            domain = [("lot_id", "=", lot.id)]
            dc = self.env["deltatech.dc"].search(domain)
            if not dc:
                dc = self.env["deltatech.dc"].create(
                    {
                        "product_id": lot.product_id.id,
                        "date": lot.production_date,
                        "lot_id": lot.id,
                    }
                )
            declarations |= dc
        return {
            "doc_ids": declarations.ids,
            "doc_model": "deltatech.dc",
            "data": data,
            "time": time,
            "docs": declarations,
            "lot": False,
        }


class ReportDCInvoicePrint(models.AbstractModel):
    _name = "report.deltatech_dc.report_dc_invoice"
    _description = "ReportDCPrint"
    _template = "deltatech_dc.report_dc_invoice"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(self._template)

        invoices = self.env[report.model].browse(docids)

        declarations = self.env["deltatech.dc"]

        product_with_lots = self.env["product.product"]
        for invoice in invoices.filtered(lambda x: x.state not in ["draft", "cancel"]):
            lots = invoice._get_invoiced_lot_values()
            for line in lots:
                lot = self.env["stock.lot"].browse(line["lot_id"])
                domain = [("lot_id", "=", lot.id)]
                dc = self.env["deltatech.dc"].search(domain)
                if not dc:
                    dc = self.env["deltatech.dc"].create(
                        {
                            "product_id": lot.product_id.id,
                            "date": lot.production_date,
                            "lot_id": lot.id,
                        }
                    )
                product_with_lots |= lot.product_id
                declarations |= dc
            for line in invoice.invoice_line_ids.filtered(
                lambda m: m.display_type not in ("line_section", "line_note")
            ):
                if line.product_id in product_with_lots:
                    continue
                if line.product_id.type != "product":
                    continue
                domain = [
                    ("product_id", "=", line.product_id.id),
                    ("date", "=", invoice.date),
                ]
                dc = self.env["deltatech.dc"].search(domain)
                if not dc:
                    dc = self.env["deltatech.dc"].create({"product_id": line.product_id.id, "date": invoice.date})
                declarations |= dc

        return {
            "doc_ids": declarations.ids,
            "doc_model": "deltatech.dc",
            "data": data,
            "time": time,
            "docs": declarations,
            "lot": False,
        }


class ReportDCPickingPrint(models.AbstractModel):
    _name = "report.deltatech_dc.report_dc_picking"
    _description = "ReportDCPrint"
    _template = "deltatech_dc.report_dc_picking"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(self._template)

        pickings = self.env[report.model].browse(docids)

        declarations = self.env["deltatech.dc"]

        product_with_lots = self.env["product.product"]
        for picking in pickings:
            for move in picking.move_ids:
                for move_line in move.move_line_ids:
                    lot = move_line.lot_id
                    if not lot:
                        continue
                    domain = [("lot_id", "=", lot.id)]
                    dc = self.env["deltatech.dc"].search(domain)
                    if not dc:
                        dc = self.env["deltatech.dc"].create(
                            {
                                "product_id": lot.product_id.id,
                                "date": lot.production_date or fields.Date.today(),
                                "lot_id": lot.id,
                            }
                        )
                    product_with_lots |= lot.product_id
                    declarations |= dc

        return {
            "doc_ids": declarations.ids,
            "doc_model": "deltatech.dc",
            "data": data,
            "time": time,
            "docs": declarations,
            "lot": False,
        }
