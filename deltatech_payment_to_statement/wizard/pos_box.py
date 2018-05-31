# coding=utf-8
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.account.wizard.pos_box import CashBox

class CashBoxExtended(CashBox):
    _register = False

    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.one
    def _create_bank_statement_line(self, record):
        res = super(CashBoxExtended, self)._create_bank_statement_line(record)
        return res



class PosBoxIn(CashBoxExtended):
    _inherit = 'cash.box.in'

    def _calculate_values_for_statement_line(self, record):
        values = super(PosBoxIn, self)._calculate_values_for_statement_line(record=record)
        if self.partner_id:
            values['partner_id'] = self.partner_id.id
        return values


class PosBoxOut(CashBoxExtended):
    _inherit = 'cash.box.out'

    partner_id = fields.Many2one('res.partner', string='Partner')

    def _calculate_values_for_statement_line(self, record):
        values = super(PosBoxOut, self)._calculate_values_for_statement_line(record=record)
        if self.partner_id:
            values['partner_id'] = self.partner_id.id
        return values


