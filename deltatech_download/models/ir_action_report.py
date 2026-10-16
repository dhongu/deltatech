# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    direct_download = fields.Boolean()

    def _get_readable_fields(self):
        # the web client needs the flag to decide between opening the PDF in a new tab or downloading it
        return super()._get_readable_fields() | {"direct_download"}

    def report_action(self, docids, data=None, config=True):
        action = super().report_action(docids, data=data, config=config)
        if action.get("type") == "ir.actions.report":
            action["direct_download"] = self.direct_download
        else:
            report_action = (action.get("context") or {}).get("report_action")
            if isinstance(report_action, dict):
                report_action["direct_download"] = self.direct_download
        return action
