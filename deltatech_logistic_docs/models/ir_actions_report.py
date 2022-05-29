# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def retrieve_attachment(self, record):
        if self.report_name == "account.report_original_vendor_bill" and not record.message_main_attachment_id:
            domain = record.get_attachment_domain()
            # domain = expression.AND([('mimetype','=','application/pdf'), domain])
            attachment = self.env["ir.attachment"].search(domain, limit=1)
            if attachment:
                return attachment
        return super(IrActionsReport, self).retrieve_attachment(record)
