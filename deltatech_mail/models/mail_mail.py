# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.multi
    def _send_prepare_values(self, partner=None):

        res = super(MailMail, self)._send_prepare_values(partner)
        model = self.model
        if model:
            substitutions = self.env['mail.substitution'].search([('name', '=', model)])
        else:
            substitutions = self.env['mail.substitution'].search([])

        if substitutions:
            email_to = []
            if model:
                for substitution in substitutions:
                    email_to += [substitution.email]
            else:
                for substitution in substitutions:
                    if substitution in self.message_id:
                        email_to += [substitution.email]
            if email_to:
                res['email_to'] = email_to

        return res
