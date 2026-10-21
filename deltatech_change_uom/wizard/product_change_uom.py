# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.tools import SQL


class ProductChangeUoM(models.TransientModel):
    _name = "product.change.uom"
    _description = "Product Change Uom"

    uom_id = fields.Many2one(
        "uom.uom",
        "Unit of Measure",
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if active_id:
            product = self.env["product.template"].browse(active_id)
            defaults["uom_id"] = product.uom_id.id

        return defaults

    def _replace_uom(self, model, field, variants, old_uom):
        lines = self.env[model].search([("product_id", "in", variants.ids), (field, "=", old_uom.id)])
        if lines:
            table = self.env[model]._table
            self.env.cr.execute(
                SQL(
                    "UPDATE %s SET %s = %s WHERE id IN %s",
                    SQL.identifier(table),
                    SQL.identifier(field),
                    self.uom_id.id,
                    tuple(lines.ids),
                )
            )
            lines.invalidate_recordset([field])

    def do_change(self):
        active_id = self.env.context.get("active_id", False)
        if active_id:
            product = self.env["product.template"].browse(active_id)
            variants = product.product_variant_ids
            old_uom = product.uom_id

            # inlocuire in comenzi de achizitie, comenzi de vanzare, facturi si miscari de stoc
            self._replace_uom("purchase.order.line", "product_uom_id", variants, old_uom)
            self._replace_uom("sale.order.line", "product_uom_id", variants, old_uom)
            self._replace_uom("account.move.line", "product_uom_id", variants, old_uom)
            self._replace_uom("stock.move", "product_uom", variants, old_uom)
            self._replace_uom("stock.move.line", "product_uom_id", variants, old_uom)

            # inlocuire in lista de furnizori (unitatea de achizitie din 19.0)
            sellers = product.seller_ids.filtered(lambda s: s.product_uom_id == old_uom)
            if sellers:
                self.env.cr.execute(
                    SQL(
                        "UPDATE product_supplierinfo SET product_uom_id = %s WHERE id IN %s",
                        self.uom_id.id,
                        tuple(sellers.ids),
                    )
                )
                sellers.invalidate_recordset(["product_uom_id"])

            self.env.cr.execute(
                SQL("UPDATE product_template SET uom_id = %s WHERE id = %s", self.uom_id.id, product.id)
            )
            product.invalidate_recordset(["uom_id"])
            variants.invalidate_recordset(["uom_id"])
