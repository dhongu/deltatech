from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class promissory_note(models.Model):
    _name = 'promissory.note'
    _description = "Promissory Note"
    _order = 'date_due'

    state = fields.Selection([('not_cashed', 'Not Cashed'), ('cashed', 'Cashed')], default="not_cashed",
                             string='Status', copy=False)

    type = fields.Selection([('vendor', 'Vendor'), ('customer', 'Customer')], required=True, default="customer",
                            string='Type')

    agreement = fields.Char(string="Agreement",
                            help="Agrement with date and number of rate. Ex:  CTR. 422 S / 30.05.2017  12 RATE")

    name = fields.Char(string="Series and number", readonly=True, states={'not_cashed': [('readonly', False)]},
                       required=True,
                       index=True)

    date_due = fields.Date(string='Due Date', required=True, readonly=True,
                           states={'not_cashed': [('readonly', False)]}, index=True)

    issuer_id = fields.Many2one('res.partner', string='Issuer', readonly=True,
                                states={'not_cashed': [('readonly', False)]}, required=True)
    beneficiary_id = fields.Many2one('res.partner', string='Beneficiary', readonly=True,
                                     states={'not_cashed': [('readonly', False)]}, required=True)

    invoice_id = fields.Many2one('account.invoice', string="Invoice")

    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'), default="", readonly=True,
                          states={'not_cashed': [('readonly', False)]}, required=True)

    cashed_amount = fields.Float(string='Cashed Amount', digits=dp.get_precision('Account'))
    cashed_date = fields.Date(string="Cashed Date")


    currency_id = fields.Many2one('res.currency', string="Currency", required=True, readonly=True,
                                  states={'not_cashed': [('readonly', False)]},
                                  domain=[('name', 'in', ['RON', 'EUR'])])

    acc_issuer = fields.Char('Bank Account Issuer', size=64, readonly=True,
                             states={'not_cashed': [('readonly', False)]}, required=True)
    acc_beneficiary = fields.Char('Bank Account Beneficiary', size=64, readonly=True,
                                  states={'not_cashed': [('readonly', False)]}, required=True)
    
    bank_issuer = fields.Char('Bank Issuer', size=64, readonly=True,
                             states={'not_cashed': [('readonly', False)]}, required=True)
    bank_beneficiary = fields.Char('Bank Beneficiary', size=64, readonly=True,
                                  states={'not_cashed': [('readonly', False)]}, required=True)

    note = fields.Text(string='Note')

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'customer':
            if self.beneficiary_id <> self.env.user.company_id.partner_id:
                self.issuer_id = self.beneficiary_id
            else:
                self.issuer_id = False
            self.beneficiary_id = self.env.user.company_id.partner_id
        else:
            if self.issuer_id <> self.env.user.company_id.partner_id:
                self.beneficiary_id = self.issuer_id
            else:
                self.beneficiary_id = False
            self.issuer_id = self.env.user.company_id.partner_id

    @api.onchange('issuer_id')
    def onchange_issuer_id(self):
        if self.issuer_id and self.issuer_id.bank_ids:
            self.acc_issuer = self.issuer_id.bank_ids[0].acc_number
        else:
            self.acc_issuer = False

    @api.onchange('beneficiary_id')
    def onchange_beneficiary_id(self):
        if self.issuer_id and self.beneficiary_id.bank_ids:
            self.acc_beneficiary = self.beneficiary_id.bank_ids[0].acc_number
        else:
            self.acc_beneficiary = False

    @api.multi
    def action_cashed(self):
        self.write({'state': 'cashed'})

    @api.multi
    def action_not_cashed(self):
        self.write({'state': 'not_cashed'})
    
    @api.one
    @api.constrains('amount')
    def _check_values(self):
        if self.amount <= 0.0:
            raise Warning(_('Campul <Valoare> trebuie sa fie mai mare decat 0!'))
