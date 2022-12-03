# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_domain_locations(self):
        if self.env.context.get("all_warehouses"):
            self = self.with_context(warehouse=False)
        if self.env.context.get("all_locations"):
            self = self.with_context(location=False)
        return super(ProductProduct, self)._get_domain_locations()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):

        website = self.env["website"].get_current_website()
        location = website.sudo().location_id
        warehouse = website.sudo().warehouse_id
        self = self.with_context(location=location.id, warehouse=warehouse.id)
        if not warehouse:
            self = self.with_context(all_warehouses=True)
        if not location:
            self = self.with_context(all_locations=True)

        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        # if not self.env.context.get("website_sale_stock_get_quantity"):
        #     return combination_info
        # if combination_info["product_id"]:
        #     product = self.env["product.product"].sudo().browse(combination_info["product_id"])
        #     free_qty = product.with_context(location=location.id, warehouse=warehouse.id).free_qty
        #     combination_info.update(
        #         {
        #             "virtual_available": free_qty,
        #             "virtual_available_formatted": self.env["ir.qweb.field.float"].value_to_html(
        #                 free_qty, {"precision": 0}
        #             ),
        #         }
        #     )

        return combination_info
