# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductChangeUoM(models.TransientModel):
    _name = "product.change.uom"
    _description = "Product Change Uom"

    uom_id = fields.Many2one(
        "uom.uom",
        "Unit of Measure",
        required=True,
    )
    uom_po_id = fields.Many2one("uom.uom", "Purchase Unit of Measure", required=True)

    @api.onchange("uom_id")
    def _onchange_uom_id(self):
        if self.uom_id:
            self.uom_po_id = self.uom_id.id

    @api.onchange("uom_po_id")
    def _onchange_uom(self):
        if self.uom_id and self.uom_po_id and self.uom_id.category_id != self.uom_po_id.category_id:
            self.uom_po_id = self.uom_id

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if active_id:
            product = self.env["product.template"].browse(active_id)
            defaults["uom_id"] = product.uom_id.id
            defaults["uom_po_id"] = product.uom_po_id.id

        return defaults

    def do_change(self):
        active_id = self.env.context.get("active_id", False)
        if active_id:
            product = self.env["product.template"].browse(active_id)
            variants = product.product_variant_ids

            # inlocuire in comanda de achizitie
            domain = [
                ("product_id", "in", variants.ids),
                ("product_uom", "=", product.uom_po_id.id),
            ]
            purchase_lines = self.env["purchase.order.line"].search(domain)
            if purchase_lines:
                query_dic = {
                    "ids": tuple(purchase_lines.ids),
                    "product_uom": self.uom_po_id.id,
                }
                query = "UPDATE purchase_order_line SET product_uom = %(product_uom)s WHERE id in %(ids)s"
                self._cr.execute(query, query_dic)

            # inlocuire in comanda de vanzare
            domain = [
                ("product_id", "in", variants.ids),
                ("product_uom", "=", product.uom_id.id),
            ]
            sal_order_lines = self.env["sale.order.line"].search(domain)
            if sal_order_lines:
                query_dic = {
                    "ids": tuple(sal_order_lines.ids),
                    "product_uom": self.uom_id.id,
                }
                query = "UPDATE sale_order_line SET product_uom = %(product_uom)s WHERE id in %(ids)s"
                self._cr.execute(query, query_dic)

            # inlocuire in facturi
            domain = [
                ("product_id", "in", variants.ids),
                ("product_uom_id", "=", product.uom_id.id),
            ]
            account_lines = self.env["account.move.line"].search(domain)
            if account_lines:
                query_dic = {
                    "ids": tuple(account_lines.ids),
                    "product_uom_id": self.uom_id.id,
                }
                query = "UPDATE account_move_line SET product_uom_id = %(product_uom_id)s WHERE id in %(ids)s"
                self._cr.execute(query, query_dic)

            # inlocuire in miscari de stoc
            domain = [
                ("product_id", "in", variants.ids),
                ("product_uom", "=", product.uom_id.id),
            ]
            stock_moves = self.env["stock.move"].search(domain)
            if stock_moves:
                query_dic = {
                    "ids": tuple(stock_moves.ids),
                    "product_uom": self.uom_id.id,
                }
                query = "UPDATE stock_move SET product_uom = %(product_uom)s WHERE id in %(ids)s"
                self._cr.execute(query, query_dic)

            # inlocuire in miscari de stoc
            domain = [
                ("product_id", "in", variants.ids),
                ("product_uom_id", "=", product.uom_id.id),
            ]
            stock_move_lines = self.env["stock.move.line"].search(domain)
            if stock_move_lines:
                query_dic = {
                    "ids": tuple(stock_move_lines.ids),
                    "product_uom_id": self.uom_id.id,
                }
                query = "UPDATE stock_move_line SET product_uom_id = %(product_uom_id)s WHERE id in %(ids)s"
                self._cr.execute(query, query_dic)

            query_dic = {
                "id": product.id,
                "uom_id": self.uom_id.id,
                "uom_po_id": self.uom_po_id.id,
            }
            query = "UPDATE product_template SET uom_id = %(uom_id)s, uom_po_id = %(uom_po_id)s  WHERE id = %(id)s"
            self._cr.execute(query, query_dic)
