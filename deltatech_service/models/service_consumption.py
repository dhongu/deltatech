# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class service_consumption(models.Model):
    _name = 'service.consumption'
    _description = "Service consumption"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
 
    name = fields.Char(string='Reference', index=True, readonly=True)

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, readonly=True)
    
    period_id = fields.Many2one('date.range', string='Period', required=True,
          copy=False, readonly=True )


  
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete='restrict',
                                  readonly=True,  index=True, domain=[('type', '=', 'service')] )

    quantity = fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure'), 
                            readonly=True, states={'draft': [('readonly', False)]},
                            required=True, default=1)
    invoiced_qty = fields.Float(string='Invoiced Quantity', digits= dp.get_precision('Product Unit of Measure'), 
                            readonly=True, default=0.0)

 
    price_unit = fields.Float(string='Unit Price', required=True, digits= dp.get_precision('Service Price'),
                              readonly=True, states={'draft': [('readonly', False)]},
                                default=1) 

    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=_default_currency,
                                  readonly=True, states={'draft': [('readonly', False)]},
                                  ) 
    
    state = fields.Selection([
            ('draft','Without invoice'),
            ("none", "Not Applicable"),
            ('done','With invoice'),
        ], string='Status', index=True,  default='draft', copy=False, readonly=True, states={'draft': [('readonly', False)]} )
 
    
    agreement_id = fields.Many2one('service.agreement', string='Agreement', readonly=True, ondelete='restrict', copy=False, index=True )
    agreement_line_id = fields.Many2one('service.agreement.line', string='Agreement Line', readonly=True, ondelete='restrict', copy=False )
    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference',  ondelete='set default', readonly=True, copy=False,  index=True )

    uom_id = fields.Many2one('product.uom', string='Unit of Measure', related='agreement_line_id.uom_id', readonly=True, copy=False )

    date_invoice = fields.Date(string='Invoice Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', related='agreement_id.company_id', store=True,
                                 readonly=True, related_sudo=False)

    _sql_constraints = [
        ('agreement_line_period_uniq', 'unique(period_id,agreement_line_id)',
            'Agreement line in period already exist!'),
    ]
    group_id = fields.Many2one('service.agreement.group', string="Service Group", readonly=True, ondelete='restrict', copy=False, index=True )

 


 
    @api.multi
    def unlink(self):
        for item in self:
            if item.state == 'done':
                raise Warning(_('You cannot delete a service consumption which is invoiced.'))
        return super(service_consumption, self).unlink()       
 
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 