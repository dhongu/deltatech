# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    ral_id = fields.Many2one(
        "product.product",
        "RAL",
        states={"draft": [("readonly", False)], "confirmed": [("readonly", False)]},
        readonly=True,
        domain=[("default_code", "like", "RAL%")],
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        # determinare produs RAL in functie de atributul culoare pe care il are produsul selectat

        attribute_values_ids = self.product_id.product_template_variant_value_ids.mapped("product_attribute_value_id")

        if attribute_values_ids:
            color = attribute_values_ids.filtered(lambda x: x.attribute_id.display_type == "color")
            if color:
                color = color[0]
                ral = self.env["product.product"].search([("default_code", "like", "RAL %s" % color.name)], limit=1)
                if ral:
                    self.ral_id = ral
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for mrp in res:
            mrp._onchange_product_id()
            mrp.onchange_ral_id()
        return res

    def action_generate_serial(self):
        super().action_generate_serial()
        if self.lot_producing_id and self.ral_id:
            self.lot_producing_id.write({"ral_id": self.ral_id.id})

    @api.onchange("ral_id")
    def onchange_ral_id(self):
        if self.ral_id:
            for move in self.move_raw_ids:
                if move.bom_line_id.product_id.default_code == "RAL 0000":
                    move.product_id = self.ral_id

    def _generate_moves(self):
        super()._generate_moves()
        self.onchange_ral_id()
