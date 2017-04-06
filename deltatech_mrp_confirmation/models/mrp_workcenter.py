# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    operator_ids = fields.One2many('mrp.workcenter.operator', 'workcenter_id', string='Operators')


class MrpWorkcenterOperator(models.Model):
    _name = 'mrp.workcenter.operator'
    _description = 'Work Center Operator'
    _order = "to_date DESC"

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', required=True)
    partner_id = fields.Many2one('res.partner', string="Operator")
    from_date = fields.Date(string="Form Date", default=lambda *a: fields.Date.today())
    to_date = fields.Date(string="To Date", default='2999-12-31')


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    partner_id = fields.Many2one('res.partner', string="Operator", domain="[('id', 'in', possible_partner_ids[0][2])]")
    possible_partner_ids = fields.Many2many('res.partner', compute='_get_possible_partner_ids', readonly=True)
    amount = fields.Float(string="Amount")  # , compute='_get_amount')

    """
    @api.multi
    def _get_amount(self):
        self.amount = self.duration * 1 #self.workcenter_id.costs_hour
    """



    @api.one
    def _get_possible_partner_ids(self):
        partners = self.env['res.partner']
        for operator in self.workcenter_id.operator_ids:
            if operator.from_date <= fields.Date.today() <= operator.to_date:
                partners |= operator.partner_id
        self.possible_partner_ids = partners


    @api.multi
    def action_start_working(self):
        super(MrpWorkcenterProductivity, self).action_start_working()
        for work in self:
            if not work.partner_id:
                if len(work.possible_partner_ids) == 1:
                    partner_id = work.possible_partner_ids[0]
                    work.write({'partner_id': partner_id.id})
        return True