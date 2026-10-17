# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

import time

from odoo import api, fields, models


def _get_or_create_dc(env, product, date, company, lot=None):
    """Return the declaration of the source company, creating it if missing."""
    dc_model = env["deltatech.dc"].with_company(company)
    domain = [("company_id", "=", company.id)]
    if lot:
        domain += [("lot_id", "=", lot.id)]
    else:
        domain += [("product_id", "=", product.id), ("date", "=", date), ("lot_id", "=", False)]
    dc = dc_model.search(domain)
    if not dc:
        vals = {"product_id": product.id, "date": date, "company_id": company.id}
        if lot:
            vals["lot_id"] = lot.id
        dc = dc_model.create(vals)
    return dc


def _lot_dc_date(env, lot):
    return lot.production_date or fields.Date.context_today(env["deltatech.dc"])


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
            company = lot.company_id or self.env.company
            declarations |= _get_or_create_dc(self.env, lot.product_id, _lot_dc_date(self.env, lot), company, lot=lot)
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
            company = invoice.company_id
            lots = invoice._get_invoiced_lot_values()
            for line in lots:
                lot = self.env["stock.lot"].browse(line["lot_id"])
                dc = _get_or_create_dc(self.env, lot.product_id, _lot_dc_date(self.env, lot), company, lot=lot)
                product_with_lots |= lot.product_id
                declarations |= dc
            for line in invoice.invoice_line_ids.filtered(
                lambda m: m.display_type not in ("line_section", "line_note")
            ):
                if line.product_id in product_with_lots:
                    continue
                if line.product_id.type == "service":
                    continue
                declarations |= _get_or_create_dc(self.env, line.product_id, invoice.date, company)

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
            company = picking.company_id
            for move in picking.move_ids:
                for move_line in move.move_line_ids:
                    lot = move_line.lot_id
                    if lot:
                        dc = _get_or_create_dc(self.env, lot.product_id, _lot_dc_date(self.env, lot), company, lot=lot)
                        product_with_lots |= lot.product_id
                        declarations |= dc
                    else:
                        if move_line.product_id in product_with_lots:
                            continue
                        if move_line.product_id.type == "service":
                            continue
                        date = picking.date_done or fields.Date.today()
                        dc = _get_or_create_dc(self.env, move_line.product_id, date, company)
                        product_with_lots |= move_line.product_id
                        declarations |= dc

        return {
            "doc_ids": declarations.ids,
            "doc_model": "deltatech.dc",
            "data": data,
            "time": time,
            "docs": declarations,
            "lot": False,
        }
