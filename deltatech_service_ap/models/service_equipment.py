# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
import math
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class service_equipment(models.Model):
    _description = "Apartment"
    _inherit = 'service.equipment'


    group_id = fields.Many2one('service.agreement.group', string="Building")

    @api.multi
    def _update_labels(self):
        translations = self.env['ir.translation'].search([('module','like','service'),('source','like','Equipment')])
        translations.unlink()
        translations = self.env['ir.translation'].search([('module', 'like', 'service'), ('source', 'like', 'Service Group')])
        translations.unlink()



class service_equipment_category(models.Model):
    _inherit = 'service.equipment.category'
    _description = "Apartment Category"
    name = fields.Char(string='Category', translate=True)



class service_equipment_type(models.Model):
    _inherit = 'service.equipment.type'
    _description = "Apartment Type"
