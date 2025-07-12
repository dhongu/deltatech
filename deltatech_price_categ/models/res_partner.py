from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_product_pricelist = fields.Many2one(
        search="_search_product_pricelist",  # <-- ADĂUGAT!
    )

    def _search_product_pricelist(self, operator, value):
        if operator not in ("=", "!=", "in", "not in"):
            raise NotImplementedError(f"Operatorul '{operator}' nu este suportat.")

        prop_model = self.env["ir.property"]
        pricelist_field = "property_product_pricelist"

        # Folosim o abordare directă pentru a găsi proprietățile
        props = prop_model._get_domain(pricelist_field, self._name)
        if props:
            domain = props + [("value_reference", "=", f"product.pricelist,{value}")]
            props = prop_model.search(domain)
        else:
            props = prop_model.browse()

        # Extragem id-urile partenerilor pentru care e setat explicit
        partner_ids = []
        for prop in props:
            if prop.res_id and prop.res_id.startswith("res.partner,"):
                try:
                    partner_id = int(prop.res_id.split(",")[1])
                    partner_ids.append(partner_id)
                except (ValueError, IndexError):
                    continue

        if operator == "=":
            return [("id", "in", partner_ids)]
        else:
            return [("id", "not in", partner_ids)]
