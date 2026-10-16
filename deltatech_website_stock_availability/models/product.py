# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_delay_safety = fields.Float("Customer Safety Lead Time", default=1)
    hide_out_of_stock_message = fields.Boolean(
        string="Hide Out-of-Stock Message",
        help="Do not show the 'Out of stock' website message for this product, "
        "even when it has no own or vendor availability.",
    )

    def _get_website_availability_seller(self, product):
        """Supplier used for the vendor stock and lead time shown on the website.

        Only suppliers of the website company, of an active vendor, for this variant
        (or the whole template) and not expired are considered. A currently valid
        offer is preferred; otherwise the earliest future offer is used.
        """
        website = self.env["website"].get_current_website()
        company = website.company_id or self.env.company
        today = fields.Date.context_today(self)
        sellers = product.with_company(company)._prepare_sellers()
        sellers = sellers.filtered(lambda s: not s.date_end or s.date_end >= today)
        current = sellers.filtered(lambda s: not s.date_start or s.date_start <= today)
        if current:
            return current[:1]
        return sellers.sorted(lambda s: s.date_start)[:1]

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1.0,
        uom_id=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            uom_id=uom_id,
            only_template=only_template,
        )

        if not self.env.context.get("website_sale_stock_get_quantity"):
            return combination_info

        if "free_qty" not in combination_info and combination_info.get("product_id"):
            product = self.env["product.product"].sudo().browse(combination_info["product_id"])
            website = self.env["website"].get_current_website()
            combination_info["free_qty"] = website._get_product_available_qty(product)

        combination_info["lead_time"] = 0
        if combination_info["product_id"]:
            product = self.env["product.product"].sudo().browse(combination_info["product_id"])
            seller = self._get_website_availability_seller(product)
            today = fields.Date.context_today(self)
            company_lead_time = 0
            supplier_lead_time = seller.delay or 0
            availability_vendor = seller.qty_available or 0

            combination_info["sale_delay"] = product.sale_delay
            combination_info["sale_delay_safety"] = product.sale_delay_safety
            combination_info["purchase_lead_time"] = company_lead_time + supplier_lead_time
            combination_info["availability_vendor"] = availability_vendor
            combination_info["product_template"] = self.id
            combination_info["hide_out_of_stock_message"] = self.hide_out_of_stock_message
            if seller.date_start and seller.date_start > today:
                days = (seller.date_start - today).days
                combination_info["purchase_lead_time"] += days
            # de pus un paramentru in configurare
            # if not availability_vendor:
            #     combination_info["allow_out_of_stock_order"] = False

        return combination_info
