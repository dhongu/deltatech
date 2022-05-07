# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class BlogPost(models.Model):
    _inherit = "blog.post"

    _order = "published_date desc, id DESC"
