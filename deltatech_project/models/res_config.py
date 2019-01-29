# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_equal_distribution_percentage = fields.Boolean('Equal distribution', default=True,
                                                       help='Use the equal distribution percentage between task')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        use_equal_distribution_percentage = literal_eval(
            get_param('project.use_equal_distribution_percentage', default='False'))

        res.update(use_equal_distribution_percentage=use_equal_distribution_percentage, )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('project.use_equal_distribution_percentage', repr(self.use_equal_distribution_percentage))
