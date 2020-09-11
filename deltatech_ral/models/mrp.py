# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    ral_id = fields.Many2one(
        "product.product",
        "RAL",
        states={"confirmed": [("readonly", False)]},
        readonly=True,
        domain=[("default_code", "like", "RAL%")],
    )

    @api.multi
    def action_confirm(self):

        picking_id = super(MrpProduction, self).action_confirm()

        for production in self:
            if production.ral_id and production.product_id.track_production:
                for move in production.move_created_ids:
                    if not move.restrict_lot_id:
                        prodlot_id = self.env["stock.production.lot"].create(
                            {
                                "product_id": production.product_id.id,
                                "prefix": production.ral_id.default_code,
                                "ral_id": production.ral_id.id,
                                "date": production.date_planned,
                            }
                        )
                        move.write({"restrict_lot_id": prodlot_id})
                    elif not move.restrict_lot_id.ral_id:
                        move.prodlot_id.write(
                            {"prefix": production.ral_id.default_code, "ral_id": production.ral_id.id}
                        )

        return picking_id

    @api.onchange("ral_id")
    def onchange_ral_id(self):
        if self.ral_id:
            for move in self.move_raw_ids:
                if move.bom_line_id.product_id.default_code == "RAL 0000":
                    move.product_id = self.ral_id

    @api.multi
    def _generate_moves(self):
        super(MrpProduction, self)._generate_moves()
        self.onchange_ral_id()


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    @api.model
    def _get_lot_id(self):

        production = self.env["mrp.production"].browse(self._context["active_id"])

        prodlot_id = None
        if production.ral_id and production.product_id.tracking == "lot":
            produce_move = production.move_finished_ids.filtered(lambda x: x.product_id == production.product_id.id)

            for move_line in produce_move.move_line_ids:
                if move_line.lot_id:
                    prodlot_id = move_line.lot_id

            if not prodlot_id:
                prodlot_id = self.env["stock.production.lot"].create(
                    {
                        "product_id": production.product_id.id,
                        "prefix": production.ral_id.default_code,
                        "ral_id": production.ral_id.id,
                        "date": production.date_planned_start,
                    }
                )

        return prodlot_id

    lot_id = fields.Many2one("stock.production.lot", default=_get_lot_id)
