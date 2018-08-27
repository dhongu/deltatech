# coding=utf-8



from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class Department(models.Model):
    _inherit = "hr.department"

    type = fields.Selection([('div', 'Division'),('dep','Department'),('for','Formation')])


class Holidays(models.Model):
    _inherit = "hr.holidays"


    @api.model
    def default_get(self, fields_list):
        default = super(Holidays, self).default_get(fields_list)

        if 'default_date' in self.env.context:
            default['date_from'] = self.env.context['default_date']
            default['date_to'] = self.env.context['default_date']

        return default
