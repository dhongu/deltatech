# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import time

from odoo import api, models


class PickingDelivery(models.AbstractModel):
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

    #     def __init__(self, cr, uid, name, context):
    #         super(PickingDelivery, self).__init__(cr, uid, name, context=context)
    #         self.localcontext.update({"time": time, "warranty_text": self._get_warranty_text})
    #
    def _get_warranty_text(self, product_id):
        categ = product_id.categ_id
        while categ and not categ.warranty_header:
            categ = categ.parent_id
        return {"categ": categ}


class ReportDelivery(models.AbstractModel):
    _name = "report.deltatech_stock_sn.report_warranty"
    _inherit = "report.abstract_report"
    _template = "deltatech_stock_sn.report_warranty"
    _wrapped_report_class = PickingDelivery
