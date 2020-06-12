# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _



class service_equipment(models.Model):
    _inherit = 'service.equipment'

    internal_type = fields.Selection(selection_add=[('building', 'Building')])


