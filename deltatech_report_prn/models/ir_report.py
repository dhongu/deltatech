# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(selection_add=[("qweb-prn", "PRN")], ondelete={"qweb-prn": "set default"})

    @api.model
    def _render_qweb_prn(self, report_ref, docids, data=None):
        if not data:
            data = {}
        data.setdefault("report_type", "text")
        report = self._get_report(report_ref)
        data = self._get_rendering_context(report, docids, data)
        return self._render_template(report.report_name, data), "text"
