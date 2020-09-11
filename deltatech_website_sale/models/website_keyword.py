# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class WebsiteUserSearch(models.Model):
    _name = "website.user.search"
    _description = "User search history"
    _order = "date desc"

    user_id = fields.Many2one("res.users", string="User")
    date = fields.Datetime(default=fields.Datetime.now)
    word = fields.Char()
