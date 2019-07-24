# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models

class MailMail(models.Model):
    _inherit = 'mail.mail'


    @api.multi
    def _send_prepare_values(self, partner=None):

        res = super(MailMail, self)._send_prepare_values(partner)

        substitutions = self.env['mail.substitution'].search([('name','=',self.model)])

        if substitutions:
            res['email_to'] = []
            for substitution in substitutions:
                res['email_to'] += [substitution.email]


        return  res