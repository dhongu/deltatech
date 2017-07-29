import base64

import bc
from odoo import models, fields, api, _
from odoo.exceptions import Warning

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class woody_wizard(models.TransientModel):
    _name = 'woody.wizard'
    _description = "Woody Wizard"

    file_bc = fields.Binary(string="File BOM")
    filename_bc = fields.Char('File Name BOM', required=True)
    file_dc = fields.Binary(string="File Chart of Debiting")
    filename_dc = fields.Char('File Name Chart of Debiting', required=True)
    product_id = fields.Many2one('product.template', 'Product')

    @api.multi
    def do_import(self):
        file_bc = base64.b64decode(self.file_bc)
        file_dc = base64.b64decode(self.file_dc)

        woody_data = bc.extract(file_bc, file_dc)
        components = []
        for k, v in woody_data['depozit']:
            uom = self.get_uom(v[2])
            product = self.env['product.product'].search([('default_code', '=', v[1])])
            if not product:
                product = self.env['product.product'].create({
                    'name': v[0],
                    'default_code': v[1],
                    'uom_id': uom.id
                })
            if product.uom.category_id != uom.category_id:
                raise Warning(_('Unitatea de masura %s nu se poate utiliza pentru produsul %s') % (uom.name, product.name ))




    @api.model
    def get_uom(self, mUnit):
        unit = self.env['product.uom'].search([('name', '=', mUnit)])
        if not unit:
            raise Warning(_('Please create UOM %s') % mUnit)
        return unit.id
