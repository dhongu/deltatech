from odoo import fields, models


class PricelistWizard(models.TransientModel):
    _name = "pricelist.wizard"
    _description = "Pricelist Wizard"

    public_category_id = fields.Many2one("product.public.category", string="Public Category", required=True)
    add_to_children = fields.Boolean(string="Add to Children Categories", default=True)

    def apply_category_to_products(self):
        pricelist_id = self.env.context.get("default_pricelist_id")
        if pricelist_id:
            pricelist = self.env["product.pricelist"].browse(pricelist_id)
            for line in pricelist.item_ids:
                if line.applied_on == "1_product" and line.product_tmpl_id:
                    line.product_tmpl_id.write({"public_categ_ids": [(4, self.public_category_id.id)]})
                elif line.applied_on == "2_product_category" and line.categ_id:
                    self._add_category_to_products(line.categ_id, self.add_to_children)
                elif line.applied_on == "0_product_variant" and line.product_id:
                    line.product_id.write({"public_categ_ids": [(4, self.public_category_id.id)]})
                elif line.applied_on == "3_global":
                    continue

    def _add_category_to_products(self, category, add_to_children):
        products = self.env["product.template"].search([("categ_id", "=", category.id)])
        products.write({"public_categ_ids": [(4, self.public_category_id.id)]})
        if add_to_children:
            for child_category in category.child_id:
                self._add_category_to_products(child_category, add_to_children)
