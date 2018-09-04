# -*- coding: utf-8 -*-


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class service_config_settings(models.Model):
    _name = 'service.config.settings'
    _inherit = 'res.config.settings'

    module_deltatech_service_equipment = fields.Boolean('Use Equipments')
    module_deltatech_service_maintenance = fields.Boolean('Use maintenance')
