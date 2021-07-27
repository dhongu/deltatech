# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):

        if vals.get("tracking", "none") == "lot":
            templates_without_lot = self.filtered(lambda p: p.tracking == "none")
        else:
            templates_without_lot = False
        res = super(ProductTemplate, self).write(vals)
        if templates_without_lot:
            products = self.env["product.product"]
            for template in templates_without_lot:
                products |= template.product_variant_ids
            products.fill_lot_in_stock_docs()
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("tracking")
    def onchange_tracking(self):
        res = super(ProductProduct, self).onchange_tracking()
        if res and res.get("warning", False):
            res.pop("warning")
        return res

    def write(self, vals):
        if vals.get("tracking", "none") == "lot":
            products_without_lot = self.filtered(lambda p: p.tracking == "none")
        else:
            products_without_lot = False
        res = super(ProductProduct, self).write(vals)
        if products_without_lot:
            products_without_lot.fill_lot_in_stock_docs()
        return res

    def fill_lot_in_stock_docs(self):
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
