# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


# e posibil ca o factura sa contina mai multe contracte
class AccountInvoice(models.Model):
    _inherit = "account.move"

    agreement_id = fields.Many2one(
        "service.agreement", string="Service Agreement", related="invoice_line_ids.agreement_line_id.agreement_id"
    )

    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        consumptions = self.env["service.consumption"].search([("invoice_id", "in", self.ids)])
        if consumptions:
            consumptions.write({"state": "draft", "invoice_id": False})
            for consumption in consumptions:
                consumption.agreement_id.compute_totals()
        return res

    def unlink(self):
        consumptions = self.env["service.consumption"].search([("invoice_id", "in", self.ids)])
        if consumptions:
            consumptions.write({"state": "draft"})
            for consumption in consumptions:
                consumption.agreement_id.compute_totals()
        return super(AccountInvoice, self).unlink()

    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        agreements = self.env["service.agreement"]
        for invoice in self:
            for line in invoice.invoice_line_ids:
                agreements |= line.agreement_line_id.agreement_id
        agreements.compute_totals()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    agreement_line_id = fields.Many2one("service.agreement.line", string="Service Agreement Line")
