# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    inventory_availability = fields.Selection(
        selection_add=[("preorder", "Show inventory below a threshold and allow sales if not enough stock")]
    )

    sale_delay_safety = fields.Float("Customer Safety Lead Time", default=1)

    availability_text = fields.Char(compute="_compute_availability_text")
    is_qty_available = fields.Selection(
        [("stock", "In Stock"), ("provider", "In provider stock"), ("order", "At Order")],
        compute="_compute_availability_text",
    )

    def _compute_availability_text(self):
        for product in self:
            qty_available = product.sudo().qty_available
            inventory_availability = product.sudo().inventory_availability
            if qty_available > 0 or inventory_availability == "never":
                product.availability_text = _("In stock")
                product.is_qty_available = "stock"
            else:
                if inventory_availability != "preorder":
                    product.availability_text = _("Not in stock")
                    # product.is_qty_available = "provider"
                else:
                    product.availability_text = _("At order")
                    product.is_qty_available = "order"
                    supplier_lead_time = product.seller_ids and product.seller_ids[0].delay or 0
                    if product.seller_ids[0].date_start and product.seller_ids[0].date_start > fields.Date.today():
                        weeks = (product.seller_ids[0].date_start - fields.Date.today()).days // 7
                        if weeks > 2:
                            product.availability_text = _("Delivery in %s weeks") % weeks
                        else:
                            days = (product.seller_ids[0].date_start - fields.Date.today()).days
                            product.availability_text = _("Delivery in %s days") % days
                    elif supplier_lead_time:
                        d1 = product.sale_delay + supplier_lead_time
                        d2 = d1 + product.sale_delay_safety
                        if d1 == d2 or d1 == 0:
                            product.availability_text = _("Delivery in %s days") % int(d2)
                        else:
                            product.availability_text = _("Delivery in %s - %s days") % (int(d1), int(d2))

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        if not self.env.context.get("website_sale_stock_get_quantity"):
            return combination_info

        combination_info["lead_time"] = 0
        if combination_info["product_id"]:
            product = self.env["product.product"].sudo().browse(combination_info["product_id"])
            company_lead_time = self.sudo().env.user.company_id.po_lead
            supplier_lead_time = product.seller_ids and product.seller_ids[0].delay or 0

            combination_info["sale_delay"] = product.sale_delay
            combination_info["sale_delay_safety"] = product.sale_delay_safety
            combination_info["purchase_lead_time"] = company_lead_time + supplier_lead_time
            if (
                product.seller_ids
                and product.seller_ids[0].date_start
                and product.seller_ids[0].date_start > fields.Date.today()
            ):
                days = (product.seller_ids[0].date_start - fields.Date.today()).days
                combination_info["purchase_lead_time"] += days

            # if product.type == "product" and product.inventory_availability in ["preorder"]:
            #     lead_min = company_lead_time + supplier_lead_time + product.sale_delay
            #     lead_max = lead_min + product.sale_delay_safety
            #     interval = '%d - %s' % (lead_min, lead_max)
            #     combination_info["custom_message"] = _("Delivery in %s days") % interval

        return combination_info
