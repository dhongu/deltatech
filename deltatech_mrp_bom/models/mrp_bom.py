# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    base_type = fields.Selection(
        [("normal", "Normal"), ("base", "Base"), ("derived", "Derived")], string="Base Type", default="normal"
    )

    @api.onchange("product_tmpl_id")
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            self.product_uom_id = self.product_tmpl_id.uom_id.id
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
                bom.bom_line_ids.unlink()
                for line in base_bom.bom_line_ids:
                    new_line = line.copy()
                    new_line.bom_id = bom.id
                    line_tmpl = line.product_id.product_tmpl_id
                    combinations = self.env["product.template.attribute.value"]

                    for attribute_header in bom.product_tmpl_id.attribute_line_ids:
                        for attribute_line in line_tmpl.attribute_line_ids:
                            if attribute_header.attribute_id == attribute_line.attribute_id:
                                ptav = bom.product_id.product_template_attribute_value_ids
                                ptav = ptav.filtered(lambda x: x.attribute_id == attribute_header.attribute_id)
                                line_ptav = line_tmpl.attribute_line_ids.mapped("product_template_value_ids")
                                line_ptav = line_ptav.filtered(
                                    lambda x: x.product_attribute_value_id == ptav.product_attribute_value_id
                                )
                                combinations |= line_ptav

                    product = line_tmpl._get_variant_for_combination(combinations)
                    if product:
                        new_line.product_id = product


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
                "name": _("BOM"),
                "view_mode": "form,tree",
                "res_model": "mrp.bom",
                "view_id": False,
                "target": "current",
                "nodestroy": True,
                "type": "ir.actions.act_window",
            }
