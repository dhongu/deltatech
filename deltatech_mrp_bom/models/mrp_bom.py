# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import Command, api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    base_type = fields.Selection(
        [("normal", "Normal"), ("base", "Base"), ("derived", "Derived")], string="Base Type", default="normal"
    )

    @api.onchange("product_tmpl_id")
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            self.uom_id = self.product_tmpl_id.uom_id.id
            if self.product_id.product_tmpl_id != self.product_tmpl_id:
                self.product_id = False

            for line in self.bom_line_ids:
                bom_product_template_attribute_value_ids = self.env["product.template.attribute.value"]

                for attribute_value in line.bom_product_template_attribute_value_ids:
                    for possible_value in line.possible_bom_product_template_attribute_value_ids:
                        if attribute_value.name == possible_value.name:
                            bom_product_template_attribute_value_ids |= possible_value

                line.bom_product_template_attribute_value_ids = bom_product_template_attribute_value_ids

    def recompute_from_base(self):
        for bom in self:
            if bom.base_type != "derived":
                continue

            domain = [("product_tmpl_id", "=", bom.product_tmpl_id.id), ("base_type", "=", "base")]
            base_bom = self.search(domain, limit=1)
            if base_bom:
                bom._copy_recipe_from_base(base_bom)

    def _copy_recipe_from_base(self, base_bom):
        """Replace the recipe of a derived BoM with the one of its base BoM.

        The base yield (quantity and unit) is kept, so the components keep their proportions.
        Lines, operations and by-products restricted to other variants are skipped, the others
        are copied for the derived variant.
        """
        self.ensure_one()
        product = self.product_id
        self.bom_line_ids.unlink()
        self.byproduct_ids.unlink()
        # archived, not deleted: work orders of existing productions still point to them
        self.operation_ids.action_archive()
        self.write({"product_qty": base_bom.product_qty, "uom_id": base_bom.uom_id.id})

        operations_mapping = {}
        for operation in base_bom.operation_ids:
            if product and operation._skip_operation_line(product):
                continue
            operations_mapping[operation] = operation.copy(
                {
                    "bom_id": self.id,
                    "bom_product_template_attribute_value_ids": False,
                    "blocked_by_operation_ids": False,
                }
            )
        for operation, new_operation in operations_mapping.items():
            blocked_by = operation.blocked_by_operation_ids.filtered(lambda o: o in operations_mapping)
            if blocked_by:
                new_operation.blocked_by_operation_ids = [Command.set([operations_mapping[o].id for o in blocked_by])]

        def mapped_operation(operation):
            return operations_mapping[operation].id if operation in operations_mapping else False

        for line in base_bom.bom_line_ids:
            if product and line._skip_bom_line(product):
                continue
            line.copy(
                {
                    "bom_id": self.id,
                    "product_id": self._get_derived_component(line.product_id).id,
                    "bom_product_template_attribute_value_ids": False,
                    "operation_id": mapped_operation(line.operation_id),
                }
            )

        for byproduct in base_bom.byproduct_ids:
            if product and byproduct._skip_byproduct_line(product):
                continue
            byproduct.copy(
                {
                    "bom_id": self.id,
                    "bom_product_template_attribute_value_ids": False,
                    "operation_id": mapped_operation(byproduct.operation_id),
                }
            )

    def _get_derived_component(self, component):
        """Return the variant of the component matching the attributes of the derived product."""
        self.ensure_one()
        line_tmpl = component.product_tmpl_id
        combinations = self.env["product.template.attribute.value"]
        for attribute_header in self.product_tmpl_id.attribute_line_ids:
            for attribute_line in line_tmpl.attribute_line_ids:
                if attribute_header.attribute_id == attribute_line.attribute_id:
                    ptav = self.product_id.product_template_attribute_value_ids
                    ptav = ptav.filtered(lambda x, attribute=attribute_header.attribute_id: x.attribute_id == attribute)
                    line_ptav = line_tmpl.attribute_line_ids.mapped("product_template_value_ids")
                    line_ptav = line_ptav.filtered(
                        lambda x, value=ptav.product_attribute_value_id: x.product_attribute_value_id == value
                    )
                    combinations |= line_ptav
        return line_tmpl._get_variant_for_combination(combinations) or component


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    bom_product_template_attribute_value_ids = fields.Many2many("product.template.attribute.value", copy=True)

    def open_bom(self):
        self.ensure_one()
        if self.child_bom_id:
            # print "Deschid sublista de materiale"
            return {
                "res_id": self.child_bom_id.id,
                "domain": "[('id','=', " + str(self.child_bom_id.id) + ")]",
                "name": self.env._("BOM"),
                "view_mode": "form,list",
                "res_model": "mrp.bom",
                "view_id": False,
                "target": "current",
                "nodestroy": True,
                "type": "ir.actions.act_window",
            }
