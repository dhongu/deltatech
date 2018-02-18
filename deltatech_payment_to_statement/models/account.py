# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError




class AccountJournal(models.Model):
    _inherit = "account.journal"

    statement_sequence_id = fields.Many2one('ir.sequence', string='Statement Sequence', copy=False)