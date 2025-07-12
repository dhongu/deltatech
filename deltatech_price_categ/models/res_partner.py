from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_product_pricelist = fields.Many2one(
        search='_search_product_pricelist',  # <-- ADĂUGAT!
    )

    def _search_product_pricelist(self, operator, value):
        if operator not in ('=', '!='):
            raise NotImplementedError(f"Operatorul '{operator}' nu este suportat.")

        prop_model = self.env['ir.property']
        pricelist_field = 'property_product_pricelist'

        # Obținem toate proprietățile setate direct pentru parteneri
        props = prop_model.search([
            ('name', '=', pricelist_field),
            ('res_model', '=', 'res.partner'),
            ('value_reference', '=', f'product.pricelist,{value}')
        ])

        # Extragem id-urile partenerilor pentru care e setat explicit
        partner_ids = [int(prop.res_id.split(',')[1]) for prop in props if prop.res_id]

        if operator == '=':
            return [('id', 'in', partner_ids)]
        else:
            return [('id', 'not in', partner_ids)]
