# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_supplier_info(self, partner, line, price, currency):
        # In Odoo 20 core no longer creates vendor pricelists at PO confirmation
        # (the last confirmed PO line acts as pricelist). The helper is kept here,
        # as it was in Odoo 19 core, for the "Add supplier to product" setting.
        product = line.product_id
        return {
            "partner_id": partner.id,
            "sequence": max(product.seller_ids.mapped("sequence")) + 1 if product.seller_ids else 1,
            "min_qty": 1.0,
            "price": price,
            "currency_id": currency.id,
            "discount": line.discount,
            "delay": max(0, (line.date_planned.date() - fields.Datetime.now().date()).days),
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_id": product.id if product.product_variant_count > 1 else False,
        }

    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product (behaviour of Odoo 19 core, removed in Odoo 20), only when the setting
        # "purchase.add_supplier_to_product" is enabled.
        get_str = self.env["ir.config_parameter"].sudo().get_str
        add_supplier_to_product = safe_eval(get_str("purchase.add_supplier_to_product", "False"))
        if not add_supplier_to_product:
            return
        for order in self:
            order._add_supplier_to_product_lines()

    def _add_supplier_to_product_lines(self):
        self.ensure_one()
        supplierinfo_by_template = {}
        # Do not add a contact as a supplier
        partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
        allowed_partners = partner | self.partner_id
        for line in self.order_line:
            product = line.product_id
            is_variant = product.product_variant_count > 1
            already_seller = any(
                s.partner_id in allowed_partners and (not is_variant or s.product_id == product)
                for s in product.seller_ids
            )
            if product and not already_seller and len(product.seller_ids) <= 10:
                price = line.price_unit
                # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
                if product.product_tmpl_id.uom_id != line.uom_id:
                    default_uom = product.product_tmpl_id.uom_id
                    price = line.uom_id._compute_price(price, default_uom)

                supplierinfo = self._prepare_supplier_info(partner, line, price, line.currency_id)
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                if line.selected_seller_id:
                    supplierinfo["product_name"] = line.selected_seller_id.product_name
                    supplierinfo["product_code"] = line.selected_seller_id.product_code

                # Group supplier values per template to batch-create supplierinfo records
                supplierinfo_list = supplierinfo_by_template.setdefault(product.product_tmpl_id, [])
                product_ids = {s.get("product_id") for s in supplierinfo_list}
                if not supplierinfo_list or supplierinfo.get("product_id") not in product_ids:
                    supplierinfo_list.append(supplierinfo)

        all_supplierinfo_vals = []
        for template, supplierinfo_list in supplierinfo_by_template.items():
            # If all variant suppliers have the same price and delay,
            # create a single template-level supplier instead of multiple variant records.
            reference_supplier = supplierinfo_list[0]
            if len(supplierinfo_list) > 1 and all(
                s.get("price") == reference_supplier.get("price") and s.get("delay") == reference_supplier.get("delay")
                for s in supplierinfo_list
            ):
                supplierinfo_list = [{**reference_supplier, "product_id": False}]
            # Skip creation if a template-level supplier already exists for this partner.
            already_seller = any(s.partner_id in allowed_partners and not s.product_id for s in template.seller_ids)
            if already_seller and not supplierinfo_list[0].get("product_id"):
                continue
            all_supplierinfo_vals.extend(supplierinfo_list)

        if all_supplierinfo_vals:
            # supplier info should be added regardless of the user access rights
            self.env["product.supplierinfo"].sudo().create(all_supplierinfo_vals)

    def button_confirm(self):
        self = self.with_context(from_po_confirmation=True)
        to_confirm = self.filtered(lambda o: o.state in ["draft", "sent"])
        res = super().button_confirm()
        to_confirm.filtered(lambda o: o.state in ["purchase", "to approve"])._add_supplier_to_product()
        get_str = self.env["ir.config_parameter"].sudo().get_str
        force_price = safe_eval(get_str("purchase.force_price_at_validation", "False"))
        if force_price:
            for purchase_order in self:
                from_currency = purchase_order.currency_id
                company = purchase_order.company_id
                for line in purchase_order.order_line:
                    seller_ids = line.product_id.seller_ids or line.product_id.product_tmpl_id.seller_ids
                    price_unit = line.price_unit
                    for seller in seller_ids:
                        if seller.partner_id == purchase_order.partner_id.commercial_partner_id:
                            to_currency = seller.currency_id or self.env.user.company_id.currency_id
                            seller_price_unit = from_currency._convert(
                                price_unit,
                                to_currency,
                                company,
                                fields.Date.today(),
                            )
                            if line.product_id.product_tmpl_id.uom_id != line.uom_id:
                                default_uom = line.product_id.product_tmpl_id.uom_id
                                seller_price_unit = line.uom_id._compute_price(seller_price_unit, default_uom)
                            seller.write({"price": seller_price_unit})
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_stock_move_price_unit(self, at_date=False):
        self.ensure_one()
        price_unit = super(PurchaseOrderLine, self.with_context(date=self.date_planned))._get_stock_move_price_unit(
            at_date=at_date
        )
        return price_unit
