# coding=utf-8
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'


    radius_user_id = fields.Many2one('radius.radcheck', string = 'User Radius')



    @api.onchange('ref')
    def onchange_ref(self):
        if self.ref:
            radius_user = self.env['radius.radcheck'].search([('username','like',self.ref)], limit=1)
            if radius_user:
                self.radius_user_id = radius_user