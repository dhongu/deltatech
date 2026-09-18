from odoo import api, fields, models

from ..constants import PACKAGING_MATERIAL_TYPES


class ProductCategory(models.Model):
    _inherit = "product.category"

    packaging_material_ids = fields.One2many(
        "packaging.product.material",
        "categ_id",
        string="Packaging materials",
    )

    def _get_packaging_materials(self):
        """Materials of this category, or of the closest parent that configures some.

        The categories are used as a tree, so a configuration set on a parent covers
        every subcategory under it and only the ones that are packed differently have
        to be configured themselves.
        """
        self.ensure_one()
        category = self
        while category:
            if category.packaging_material_ids:
                return category.packaging_material_ids
            category = category.parent_id
        return self.env["packaging.product.material"]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    packaging_material_ids = fields.One2many(
        "packaging.product.material",
        "product_tmpl_id",
        string="Packaging materials",
    )
    packaging_material_no_inherit = fields.Boolean(
        string="No packaging material",
        help="The product uses no packaging material at all, even when its category "
        "configures some. Leave it unset for the product to take the materials of its "
        "category as long as it has none of its own.",
    )
    inherited_packaging_material_ids = fields.Many2many(
        "packaging.product.material",
        string="Packaging materials of the category",
        compute="_compute_inherited_packaging_material_ids",
        help="Materials the product takes from its category as long as it has none of "
        "its own. Configuring a material on the product replaces all of them.",
    )

    @api.depends(
        "packaging_material_ids",
        "packaging_material_no_inherit",
        "categ_id.packaging_material_ids",
    )
    def _compute_inherited_packaging_material_ids(self):
        for product in self:
            inherited = self.env["packaging.product.material"]
            if not product.packaging_material_ids and not product.packaging_material_no_inherit:
                if product.categ_id:
                    inherited = product.categ_id._get_packaging_materials()
            product.inherited_packaging_material_ids = inherited

    def _get_packaging_materials(self):
        """Materials to use for this product: its own, else the ones of its category.

        Resolving at read time rather than copying the materials when the product is
        created keeps every product in step with its category, whether it was added by
        hand, imported or created from the website.

        An empty configuration means "take the materials of the category", so a product
        packed in nothing at all inside a category that is packed has to say so with
        ``packaging_material_no_inherit``.
        """
        self.ensure_one()
        if self.packaging_material_ids:
            return self.packaging_material_ids
        if self.packaging_material_no_inherit or not self.categ_id:
            return self.env["packaging.product.material"]
        return self.categ_id._get_packaging_materials()


class ProductPackagingMaterial(models.Model):
    _name = "packaging.product.material"
    _description = "Packaging material used for a product"
    _order = "material_type, id"

    product_tmpl_id = fields.Many2one(
        "product.template",
        ondelete="cascade",
        index=True,
    )
    # a material is configured either for a single product or, as a default, for a
    # whole category of products
    categ_id = fields.Many2one(
        "product.category",
        string="Product category",
        ondelete="cascade",
        index=True,
    )
    material_type = fields.Selection(PACKAGING_MATERIAL_TYPES, required=True)
    # The same product can be packed one way by the vendor and another way when it
    # is shipped to the customer, so the quantity is kept per direction.
    qty_purchase = fields.Float(string="Purchase quantity", default=0.0)
    qty_sale = fields.Float(string="Sale quantity", default=0.0)

    _owner_exclusive = models.Constraint(
        "CHECK((product_tmpl_id IS NULL) != (categ_id IS NULL))",
        "A packaging material belongs either to a product or to a product category.",
    )

    def _get_qty(self, direction):
        """Quantity used for the given direction ("purchase" or "sale")."""
        self.ensure_one()
        return self.qty_purchase if direction == "purchase" else self.qty_sale
