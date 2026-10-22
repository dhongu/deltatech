# ©  2017-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    sale_user_id = fields.Many2one("res.users", string="Salesperson", compute="_compute_sale_user_id", store=True)

    commission = fields.Float(string="Commission", default=0.0)
    commission_paid = fields.Boolean(string="Commission Paid", default=False)

    @api.depends("sale_line_ids")
    def _compute_sale_user_id(self):
        for line in self:
            if line.sale_line_ids:
                line.sale_user_id = line.sale_line_ids[0].order_id.user_id
            else:
                line.sale_user_id = False
