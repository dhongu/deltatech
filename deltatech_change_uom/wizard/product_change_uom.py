# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import SQL


class ProductChangeUoM(models.TransientModel):
    _name = "product.change.uom"
    _inherit = ["deltatech.uom.domain.mixin"]
    _description = "Product Change Uom"

    uom_id = fields.Many2one(
        "uom.uom",
        "Unit of Measure",
        required=True,
    )
    purchase_uom_id = fields.Many2one(
        "uom.uom",
        "Default Purchase Unit",
        domain="[('id', 'in', purchase_allowed_uom_ids)]",
    )
    purchase_allowed_uom_ids = fields.Many2many("uom.uom", compute="_compute_purchase_allowed_uom_ids")

    @api.depends("uom_id")
    def _compute_purchase_allowed_uom_ids(self):
        for wizard in self:
            wizard.purchase_allowed_uom_ids = wizard.uom_id
        self._extend_allowed_uom_ids("purchase_allowed_uom_ids")

    def _uom_domain_product_uom(self):
        self.ensure_one()
        return self.uom_id

    @api.onchange("uom_id")
    def _onchange_uom_id(self):
        # UM de achizitie ramane doar daca se poate converti in noua UM a produsului
        if self.uom_id and self.purchase_uom_id and not self.purchase_uom_id._has_common_reference(self.uom_id):
            self.purchase_uom_id = False

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if active_id:
            product = self.env["product.template"].browse(active_id)
            defaults["uom_id"] = product.uom_id.id
            defaults["purchase_uom_id"] = product.purchase_uom_id.id

        return defaults

    def _replace_uom(self, model, field, records, uom_map):
        """Inlocuieste UM pe `records` dupa `uom_map` {UM veche: UM noua}.

        Liniile se cauta pentru toate perechile inainte de prima scriere, ca o linie
        mutata deja pe UM noua sa nu fie prinsa din nou de o alta pereche.
        """
        to_update = []
        for old_uom, new_uom in uom_map.items():
            lines = records.filtered(lambda r, old_uom=old_uom: r[field] == old_uom)
            if lines and old_uom != new_uom:
                to_update.append((lines, new_uom))
        for lines, new_uom in to_update:
            self.env.cr.execute(
                SQL(
                    "UPDATE %s SET %s = %s WHERE id IN %s",
                    SQL.identifier(self.env[model]._table),
                    SQL.identifier(field),
                    new_uom.id,
                    tuple(lines.ids),
                )
            )
            lines.invalidate_recordset([field])

    def _replace_uom_in_lines(self, model, field, variants, uom_map):
        lines = self.env[model].search([("product_id", "in", variants.ids), (field, "in", [u.id for u in uom_map])])
        self._replace_uom(model, field, lines, uom_map)

    def do_change(self):
        if not self.env.user.has_group("deltatech_change_uom.group_change_uom"):
            raise AccessError(self.env._("Only users allowed to change the unit of measure can apply this change."))
        active_id = self.env.context.get("active_id", False)
        if active_id:
            product = self.env["product.template"].browse(active_id)
            variants = product.product_variant_ids
            old_uom = product.uom_id
            old_purchase_uom = product.purchase_uom_id or old_uom
            new_purchase_uom = self.purchase_uom_id or self.uom_id
            if not new_purchase_uom._has_common_reference(self.uom_id):
                raise UserError(
                    self.env._(
                        "The purchase unit %(purchase_uom)s cannot be converted to the unit %(uom)s.",
                        purchase_uom=new_purchase_uom.name,
                        uom=self.uom_id.name,
                    )
                )

            # aceeasi mapare pe toate documentele: comanda, receptia si factura de furnizor
            # raman in aceeasi unitate (din 19.0 conversia intre unitati incompatibile nu mai da eroare)
            uom_map = {}
            if old_purchase_uom != old_uom:
                uom_map[old_purchase_uom] = new_purchase_uom
            uom_map[old_uom] = self.uom_id

            # inlocuire in comenzi de achizitie, comenzi de vanzare, facturi si miscari de stoc
            self._replace_uom_in_lines("purchase.order.line", "uom_id", variants, uom_map)
            self._replace_uom_in_lines("sale.order.line", "product_uom_id", variants, uom_map)
            self._replace_uom_in_lines("account.move.line", "product_uom_id", variants, uom_map)
            self._replace_uom_in_lines("stock.move", "uom_id", variants, uom_map)
            self._replace_uom_in_lines("stock.move.line", "uom_id", variants, uom_map)

            # inlocuire in lista de furnizori
            self._replace_uom("product.supplierinfo", "uom_id", product.seller_ids, uom_map)

            self.env.cr.execute(
                SQL(
                    "UPDATE product_template SET uom_id = %s, purchase_uom_id = %s WHERE id = %s",
                    self.uom_id.id,
                    self.purchase_uom_id.id or None,
                    product.id,
                )
            )
            product.invalidate_recordset(["uom_id", "purchase_uom_id"])
            variants.invalidate_recordset(["uom_id"])
