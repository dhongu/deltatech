from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Raport Packaging"

    product_ids = fields.One2many('product.template.lines', 'packaging_id', string='Packaging materials')


class ProductTemplateLines(models.Model):
    _name = "product.template.lines"
    _description = "Model for one2many: products_ids"

    packaging_id = fields.Many2one('product.template')
    type = fields.Selection([
        ('plastic', 'Plastic'),
        ('wood', 'Wood'),
        ('paper', 'Paper'),
        ('pet', 'Pet')
    ])
    qty = fields.Float(string='Quantity', readonly=False, default=0)

