from odoo import models


class BlogPost(models.Model):
    _inherit = "blog.post"

    _order = "published_date desc, id desc"
