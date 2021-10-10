# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class MailSubstitution(models.Model):
    _name = "mail.substitution"
    _description = "Mail Substitution"

    name = fields.Char("Related Document Model", index=True)
    email = fields.Char("Substitution", help="Substitution with this email")
