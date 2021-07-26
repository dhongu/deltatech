# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("tracking")
    def onchange_tracking(self):
        res = super(ProductProduct, self).onchange_tracking()
        if res and res.get("warning", False):
            res.pop("warning")
        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if vals.get("tracking", "none") == "lot":
            warehouses = self.env["stock.warehouse"].with_context(active_test=False).search([])
            for product in self:
                # Parse warehouses
                company = product.company_id or self.env.user.company_id
                for war in warehouses:
                    war_loc = war.lot_stock_id
                    domain = [
                        ("product_id", "=", product.id),
                        "|",
                        ("location_id", "=", war_loc.id),
                        ("location_dest_id", "=", war_loc.id),
                    ]
                    st_moves = self.env["stock.move"].search(domain)

                    if st_moves:
                        lots = st_moves.mapped("lot_ids")
                        if lots:
                            lot = lots[0]
                        else:
                            lot_name = war.code + "000001"
                            lot = self.env["stock.production.lot"].search(
                                [
                                    ("name", "=", lot_name),
                                    ("product_id", "=", product.id),
                                    ("company_id", "=", company.id),
                                ],
                                limit=1,
                            )
                            if not lot:
                                lot = self.env["stock.production.lot"].create(
                                    {
                                        "name": lot_name,
                                        "product_id": product.id,
                                        "company_id": company.id,
                                    }
                                )
                        if lot:
                            domain = [("lot_id", "=", False)] + domain
                            st_move_lines = self.env["stock.move.line"].search(domain)

                            if st_move_lines:
                                self.env.cr.execute(
                                    """update stock_move_line   set lot_id = %s  where id in %s""",
                                    (lot.id, tuple(st_move_lines.ids)),
                                )
                            quants = self.env["stock.quant"].search(
                                [
                                    ("product_id", "=", product.id),
                                    ("lot_id", "=", False),
                                    ("location_id", "=", war_loc.id),
                                ]
                            )
                            if quants:
                                self.env.cr.execute(
                                    "update stock_quant  set lot_id = %s where id in %s", (lot.id, tuple(quants.ids))
                                )

        return res
