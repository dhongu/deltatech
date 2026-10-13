# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class MailBodySubstitution(models.Model):
    _name = "mail.body.substitution"
    _description = "Mail Body Substitution"

    name = fields.Char()
    body_part = fields.Html(string="Body Part", required=True)
    substitution = fields.Html(string="Substitution", required=True)
