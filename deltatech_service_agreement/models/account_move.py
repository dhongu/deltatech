# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def action_cancel(self):
        res = super().action_cancel()
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
        return super().unlink()

    def action_post(self):
        res = super().action_post()
        agreements = self.env["service.agreement"]
        for invoice in self:
            if invoice.move_type == "out_invoice":
                invoice_agreements = self.env["service.agreement"]
                for line in invoice.invoice_line_ids:
                    invoice_agreements |= line.agreement_line_id.agreement_id

                invoice_agreements.write({"last_invoice_id": invoice.id})
                agreements |= invoice_agreements

        agreements.compute_totals()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    agreement_line_id = fields.Many2one("service.agreement.line", string="Service Agreement Line")
    agreement_id = fields.Many2one("service.agreement", related="agreement_line_id.agreement_id", store=True)
