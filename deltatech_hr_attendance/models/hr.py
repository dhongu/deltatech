# coding=utf-8



from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError

class Department(models.Model):
    _inherit = "hr.department"

    type = fields.Selection([('div', 'Division'),('dep','Department'),('for','Formation')])


class HolidaysType(models.Model):
    _inherit = "hr.holidays.status"
    _order = 'sequence'


    sequence = fields.Integer("Sequence", default=10)
    cod = fields.Char()
    global_leave = fields.Boolean()
    retrieve = fields.Boolean()

class Holidays(models.Model):
    _inherit = "hr.holidays"


    @api.model
    def default_get(self, fields_list):
        default = super(Holidays, self).default_get(fields_list)

        if 'default_date' in self.env.context:
            default_date =  self.env.context['default_date']
            if len(default_date)  == 10 :
                default_date = default_date + ' 12:00:00'
            default['date_from'] = default_date
            default['date_to'] = default_date

        return default


    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for holiday in self:
            if holiday.employee_id:
                domain = [
                    ('date_from', '<=', holiday.date_to),
                    ('date_to', '>=', holiday.date_from),
                    ('employee_id', '=', holiday.employee_id.id),
                    ('id', '!=', holiday.id),
                    ('holiday_status_id', '=', holiday.holiday_status_id.id),
                    ('state', 'not in', ['cancel', 'refuse']),
                ]
                nholidays = self.search_count(domain)
                if nholidays:
                    raise ValidationError(_('You can not have 2 leaves that overlaps on same day for the employee %s!') % holiday.employee_id.name)