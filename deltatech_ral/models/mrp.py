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

    def action_generate_serial(self):
        super(MrpProduction, self).action_generate_serial()
        if self.lot_producing_id and self.ral_id:
            self.lot_producing_id.write({"ral_id": self.ral_id.id})

    @api.onchange("ral_id")
    def onchange_ral_id(self):
        if self.ral_id:
            for move in self.move_raw_ids:
                if move.bom_line_id.product_id.default_code == "RAL 0000":
                    move.product_id = self.ral_id

    def _generate_moves(self):
        super(MrpProduction, self)._generate_moves()
        self.onchange_ral_id()
