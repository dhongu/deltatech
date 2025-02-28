from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_ro_net_weight = fields.Float()
