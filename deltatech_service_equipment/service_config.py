# -*- coding: utf-8 -*-


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class service_config_settings(models.Model):
    _inherit = 'service.config.settings'

    group_service_equipment_advanced = fields.Boolean(string="Display menu item for equipament history and meter",
                                                      implied_group='base.group_service_equipment_advanced')
