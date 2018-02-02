from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class account_analytic_transfer(models.TransientModel):
    _name = 'account.analytic.transfer'
    _description = "Account Analytic Transfer"

    from_alanytic_line = fields.Many2one('account.analytic.line', string='From line')
    from_alanytic = fields.Many2one('account.analytic.account', related='from_alanytic_line.account_id', string='From',
                                    readonly=True)
    to_alanytic = fields.Many2one('account.analytic.account', string='To')
    date = fields.Date('Date', default=fields.Date.today)
    from_amount = fields.Float(string='from amount', related='from_alanytic_line.amount', readonly=True)
    amount = fields.Float(string='Amount')

    @api.model
    def default_get(self, fields):
        defaults = super(account_analytic_transfer, self).default_get(fields)

        active_id = self.env.context.get('active_id', False)
        if active_id:
            defaults['from_alanytic_line'] = active_id
        else:
            raise Warning(_("Please select a record"))
        return defaults

    @api.multi
    def do_transfer(self):
        self.ensure_one()
        #value = {'amount': 1 * self.amount, 'date': self.date}
        #new_line = self.from_alanytic_line.copy(value)
        value = {'amount': self.amount, 'date': self.date, 'alanytic_id': self.to_alanytic.id, }
        new_line = self.from_alanytic_line.copy(value)
        #new_line = self.from_alanytic_line.copy(value)
        self.from_alanytic_line.amount = self.from_alanytic_line.amount - self.amount

        return {
            'domain': "[('id','=', " + str(new_line.id) + ")]",
            'name': _('New'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'view_id': False,
            'type': 'ir.actions.act_window',

        }
