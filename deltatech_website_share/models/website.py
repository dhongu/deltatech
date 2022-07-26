# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):

    _inherit = "website"

    website_access_ids = fields.Many2many(
        "website", relation="website_access_rel", column2="website_id", column1="website_access_id", string="Access"
    )
