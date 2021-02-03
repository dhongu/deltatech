# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    loc_rack = fields.Char("Rack", size=16)
    loc_row = fields.Char("Row", size=16)
    loc_case = fields.Char("Case", size=16)

    last_inventory_date = fields.Date(
        string="Last Inventory Date", readonly=True, compute="_compute_last_inventory", store=True
    )
    last_inventory_id = fields.Many2one(
        "stock.inventory", string="Last Inventory", readonly=True, compute="_compute_last_inventory", store=True
    )

    def get_last_inventory_date(self):
        products = self.env["product.product"]
        for template in self:
            products |= template.product_variant_ids
        products.get_last_inventory_date()

    def _compute_last_inventory(self):
        for template in self:
            last_inventory_date = False
            last_inventory_id = False
            for product in template.product_variant_ids:
                if last_inventory_date < product.last_inventory_date:
                    last_inventory_date = product.last_inventory_date
                    last_inventory_id = product.last_inventory_id
            template.last_inventory_date = last_inventory_date
            template.last_inventory_id = last_inventory_id

    def action_update_quantity_on_hand(self):
        action = super(ProductTemplate, self).action_update_quantity_on_hand()
        action_inventory_form = self.env.ref("stock.action_inventory_form").read()[0]
        action["name"] = action_inventory_form["name"]
        action["res_model"] = action_inventory_form["res_model"]
        action["view_id"] = action_inventory_form["view_id"]
        action["domain"] = []
        action["views"] = [(False, "form")]
        action["context"] = {"default_product_ids": self.product_variant_ids.ids}
        action["target"] = "new"
        action["res_id"] = False
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    last_inventory_date = fields.Date(string="Last Inventory Date", readonly=True)
    last_inventory_id = fields.Many2one("stock.inventory", string="Last Inventory", readonly=True)

    def get_last_inventory_date(self):
        for product in self:
            line = self.env["stock.inventory.line"].search(
                [("product_id", "=", product.id), ("is_ok", "=", True)], limit=1, order="id desc"
            )
            if line:
                line.set_last_last_inventory()
