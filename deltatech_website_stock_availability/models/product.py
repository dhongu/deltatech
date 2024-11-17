# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_delay_safety = fields.Float("Customer Safety Lead Time", default=1)

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1.0,
        parent_combination=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        if not self.env.context.get("website_sale_stock_get_quantity"):
            return combination_info

        combination_info["lead_time"] = 0
        if combination_info["product_id"]:
            product = self.env["product.product"].sudo().browse(combination_info["product_id"])
            company_lead_time = self.env.company.po_lead
            supplier_lead_time = product.seller_ids and product.seller_ids[0].delay or 0
            availability_vendor = product.seller_ids and product.seller_ids[0].qty_available or 0

            combination_info["sale_delay"] = product.sale_delay
            combination_info["sale_delay_safety"] = product.sale_delay_safety
            combination_info["purchase_lead_time"] = company_lead_time + supplier_lead_time
            combination_info["availability_vendor"] = availability_vendor
            if (
                product.seller_ids
                and product.seller_ids[0].date_start
                and product.seller_ids[0].date_start > fields.Date.today()
            ):
                days = (product.seller_ids[0].date_start - fields.Date.today()).days
                combination_info["purchase_lead_time"] += days

            if not availability_vendor:
                combination_info["allow_out_of_stock_order"] = False

        return combination_info
