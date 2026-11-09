# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError

TARGET_FIELD = {
    "1_product": "product_tmpl_id",
    "0_product_variant": "product_id",
    "2_product_category": "categ_id",
}


class PricelistBulkAdd(models.TransientModel):
    _name = "pricelist.bulk.add"
    _inherit = ["pricelist.formula.mixin"]
    _description = "Add Pricelist Rules for Many Products"

    pricelist_id = fields.Many2one("product.pricelist", required=True, ondelete="cascade")
    currency_id = fields.Many2one(related="pricelist_id.currency_id")
    applied_on = fields.Selection(
        selection=[
            ("1_product", "Products"),
            ("0_product_variant", "Product Variants"),
            ("2_product_category", "Product Categories"),
        ],
        string="Apply On",
        default="1_product",
        required=True,
    )
    product_tmpl_ids = fields.Many2many("product.template", string="Products")
    product_ids = fields.Many2many("product.product", string="Product Variants")
    categ_ids = fields.Many2many("product.category", string="Product Categories")
    fill_categ_ids = fields.Many2many(
        "product.category",
        relation="pricelist_bulk_add_fill_categ_rel",
        string="Add Products of Categories",
        help="Adds to the list the products of these categories and of their subcategories.",
    )
    min_quantity = fields.Float(string="Min. Quantity", digits="Product Unit")
    date_start = fields.Datetime(string="Start Date")
    date_end = fields.Datetime(string="End Date")
    existing_policy = fields.Selection(
        selection=[
            ("skip", "Keep the existing rule"),
            ("update", "Update the existing rule"),
            ("create", "Add a new rule"),
        ],
        string="If a Rule Exists",
        default="skip",
        required=True,
        help="A rule exists when the pricelist already has a rule for the same product, "
        "minimum quantity and validity period.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids") or []
        if active_model == "product.template" and active_ids:
            res.update(applied_on="1_product", product_tmpl_ids=[fields.Command.set(active_ids)])
        elif active_model == "product.product" and active_ids:
            res.update(applied_on="0_product_variant", product_ids=[fields.Command.set(active_ids)])
        return res

    @api.onchange("fill_categ_ids")
    def _onchange_fill_categ_ids(self):
        if not self.fill_categ_ids:
            return
        domain = [("categ_id", "child_of", self.fill_categ_ids.ids)]
        if self.applied_on == "0_product_variant":
            self.product_ids |= self.env["product.product"].search(domain)
        else:
            self.product_tmpl_ids |= self.env["product.template"].search(domain)
        self.fill_categ_ids = False

    def _get_targets(self):
        self.ensure_one()
        return {
            "1_product": self.product_tmpl_ids,
            "0_product_variant": self.product_ids,
            "2_product_category": self.categ_ids,
        }[self.applied_on]

    def _get_target_vals(self, target):
        vals = {"applied_on": self.applied_on, TARGET_FIELD[self.applied_on]: target.id}
        if self.applied_on == "0_product_variant":
            vals["product_tmpl_id"] = target.product_tmpl_id.id
        return vals

    def _find_existing(self, target):
        return self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.pricelist_id.id),
                ("applied_on", "=", self.applied_on),
                (TARGET_FIELD[self.applied_on], "=", target.id),
                ("min_quantity", "=", self.min_quantity),
                ("date_start", "=", self.date_start),
                ("date_end", "=", self.date_end),
            ]
        )

    def action_apply(self):
        self.ensure_one()
        targets = self._get_targets()
        if not targets:
            raise UserError(self.env._("Select at least one product or category."))
        common_vals = {
            "pricelist_id": self.pricelist_id.id,
            "min_quantity": self.min_quantity,
            "date_start": self.date_start,
            "date_end": self.date_end,
            **self._get_formula_vals(),
        }
        to_update = self.env["product.pricelist.item"]
        vals_list = []
        skipped = 0
        for target in targets:
            existing = self._find_existing(target) if self.existing_policy != "create" else False
            if existing and self.existing_policy == "skip":
                skipped += 1
            elif existing:
                to_update |= existing
            else:
                vals_list.append({**common_vals, **self._get_target_vals(target)})
        if to_update:
            to_update.write(self._get_formula_vals())
        created = self.env["product.pricelist.item"].create(vals_list)
        items = created | to_update
        message = self.env._(
            "%(created)s rules added, %(updated)s rules updated, %(skipped)s existing rules kept.",
            created=len(created),
            updated=len(to_update),
            skipped=skipped,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Pricelist %s", self.pricelist_id.display_name),
                "message": message,
                "type": "success" if items else "warning",
                "next": items._get_bulk_action() if items else {"type": "ir.actions.act_window_close"},
            },
        }
