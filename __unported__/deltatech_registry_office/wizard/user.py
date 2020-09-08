# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CreateUser(models.TransientModel):
    _name = 'wizard.partner.user'
    _description = 'Create login from partner'

    user_data = fields.One2many('wizard.user.datas', 'rel_id')

    @api.model
    def default_get(self, fields):
        res = super(CreateUser, self).default_get(fields)
        vals = []
        active_ids = self.env.context.get('active_ids', False)
        partners = self.env['res.partner'].browse(active_ids)
        for partner in partners:
            user = self.env['res.users'].search([('partner_id', '=', partner.id)], limit=1)
            if not user:
                vals.append((0, 0, {'partner_id': partner.id, 'login': partner.email or partner.name}))
        res['user_data'] = vals
        return res

    @api.multi
    def create_login(self):
        for data in self:
            vals = {}
            for da in data.user_data:
                vals = {
                    'partner_id': da.partner_id.id,
                    'login': da.login,
                    # 'groups_id': da.groups_ids
                }
                self.env['res.users'].create(vals)


class CreateUserData(models.TransientModel):
    _name = 'wizard.user.datas'

    rel_id = fields.Many2one('wizard.partner.user')
    partner_id = fields.Many2one('res.partner', string='Partner')
    login = fields.Char('Login')
    groups_ids = fields.Many2many('res.groups', column1='user_datas_id', column2="group_id", string='Groups')
