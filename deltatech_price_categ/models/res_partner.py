from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_product_pricelist = fields.Many2one(
        search='_search_product_pricelist',  # <-- ADĂUGAT!
    )

    def _search_product_pricelist(self, operator, value):
        if operator not in ('=', '!=', 'in', 'not in'):
            raise NotImplementedError(f"Operatorul '{operator}' nu este suportat.")

        prop_model = self.env['ir.property']
        pricelist_field = 'property_product_pricelist'

        # Transformăm value în listă dacă nu este deja
        if operator in ('in', 'not in'):
            pricelist_ids = value if isinstance(value, list) else [value]
        else:
            pricelist_ids = [value]

        # Pregătim domeniul pentru căutarea în ir.property
        domain = [
            ('name', '=', pricelist_field),
            ('model', '=', 'res.partner')
        ]

        # Adăugăm condiția pentru value_reference
        if len(pricelist_ids) == 1:
            domain.append(('value_reference', '=', f'product.pricelist,{pricelist_ids[0]}'))
        else:
            value_refs = [f'product.pricelist,{pid}' for pid in pricelist_ids]
            domain.append(('value_reference', 'in', value_refs))

        # Obținem toate proprietățile
        props = prop_model.search(domain)

        # Extragem id-urile partenerilor
        partner_ids = [int(prop.res_id.split(',')[1]) for prop in props if prop.res_id]

        # Construim domeniul final pentru partner
        if operator in ('=', 'in'):
            return [('id', 'in', partner_ids)]
        else:  # operator in ('!=', 'not in')
            return [('id', 'not in', partner_ids)]

