# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import time

from odoo import api, models


class WrappedReportInvoiceWarranty(models.AbstractModel):
    _name = "report.deltatech_stock_sn.report_invoice_warranty"
    _description = "WrappedReportInvoiceWarranty"
    _template = None

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(self._template)
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "time": time,
            "docs": self.env[report.model].browse(docids),
            "warranty_text": self._get_warranty_text,
        }

    def _get_warranty_text(self, product_id):
        categ = product_id.categ_id
        while categ and not categ.warranty_header:
            categ = categ.parent_id


class ReportInvoice(models.AbstractModel):
    _name = "report.deltatech_stock_sn.report_invoice_warranty"
    _inherit = "report.abstract_report"
    _template = "deltatech_stock_sn.report_invoice_warranty"
    _wrapped_report_class = WrappedReportInvoiceWarranty
