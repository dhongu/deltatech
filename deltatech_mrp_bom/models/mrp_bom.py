# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

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


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"
    # _rec_name = "name"

    bom_product_template_attribute_value_ids = fields.Many2many("product.template.attribute.value", copy=True)

    # name = fields.Char(string="Name")
    #
    # @api.onchange("product_id")
    # def onchange_product_id(self):
    #     super(MrpBomLine, self).onchange_product_id()
    #     if self.product_id:
    #         self.name = self.product_id.name
    #
    # @api.model
    # def create(self, vals):
    #     if "name" not in vals:
    #         product = self.env["product.product"].browse(vals["product_id"])
    #         vals["name"] = product.name
    #     return super(MrpBomLine, self).create(vals)

    def open_bom(self):
        self.ensure_one()
        if self.child_bom_id:
            # print "Deschid sublista de materiale"
            return {
                "res_id": self.child_bom_id.id,
                "domain": "[('id','=', " + str(self.child_bom_id.id) + ")]",
                "name": _("BOM"),
                "view_type": "form",
                "view_mode": "form,tree",
                "res_model": "mrp.bom",
                "view_id": False,
                "target": "current",
                "nodestroy": True,
                "type": "ir.actions.act_window",
            }

    #
    # def init(self):
    #     super(MrpBomLine, self).init()
    #     lines = self.search([("name", "=", False)])
    #     for line in lines:
    #         line.write({"name": line.product_id.name})
