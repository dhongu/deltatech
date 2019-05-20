# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, tools, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    vat_subjected = fields.Boolean('VAT Legal Statement')  # campu este definit si in modulele de localizare