# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning

"""
class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    def build_email(self, email_from, email_to, subject, body, email_cc=None, email_bcc=None, reply_to=False,
                    attachments=None, message_id=None, references=None, object_id=False, subtype='plain', headers=None,
                    body_alternative=None, subtype_alternative='plain'):

        if not self.env.context.get('ignore_always_only_to', False):
            get_param = self.env['ir.config_parameter'].sudo().get_param
            always_mail_to = get_param('mail.always.only.to', default=False)
            if always_mail_to:
                email_cc = []
                email_to = [always_mail_to]

        msg = super(IrMailServer, self).build_email(email_from, email_to, subject, body, email_cc, email_bcc, reply_to,
                                                    attachments, message_id, references, object_id, subtype, headers,
                                                    body_alternative, subtype_alternative)
        return msg


    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False):

        if not self.env.context.get('ignore_always_only_to',False):
            get_param = self.env['ir.config_parameter'].sudo().get_param
            always_mail_to = get_param('mail.always.only.to', default=False)
            if always_mail_to:
                message['To'] = always_mail_to
                if message['Cc']:
                    message['Cc'] = None

        message_id = super(IrMailServer, self).send_email(message, mail_server_id, smtp_server, smtp_port,
                                                          smtp_user, smtp_password, smtp_encryption, smtp_debug)
        return message_id

"""






class MailMail(models.Model):
    """ Model holding RFC2822 email messages to send. This model also provides
        facilities to queue and send new email messages.  """
    _inherit = 'mail.mail'


    @api.model_create_multi
    def create(self, vals_list):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        always_mail_to = get_param('mail.always.only.to', default=False)
        if not self.env.context.get('ignore_always_only_to', False):
            if always_mail_to:
                for values in vals_list:
                    values.update({'email_to': always_mail_to,
                                   'recipient_ids': [(5, False, False)]})
        return super(MailMail, self).create(vals_list)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
