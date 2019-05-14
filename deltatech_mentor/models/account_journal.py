# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang



class AccountJournal(models.Model):
    _inherit = "account.journal"

    serie_carnet = fields.Char(string='Serie Carnet Mentor')