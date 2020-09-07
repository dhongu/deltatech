# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    period_id = fields.Many2one('account.period', string='Force Period',
                                domain=[('state', '!=', 'done')], copy=False,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                readonly=True, states={'draft': [('readonly', False)]})

    @api.multi
    def action_move_line_create(self):
        res = super(AccountVoucher, self).action_move_line_create()
        for voucher in self:
            if not voucher.period_id:
                period = voucher.period_id
                if not period:
                    period = self.env["account.period"].find(voucher.account_date)[:1]
                voucher.write({'period_id': period.id})
        return res
