# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    favorite = fields.Boolean()