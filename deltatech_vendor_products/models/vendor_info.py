# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import _, api, fields, models, tools

_logger = logging.getLogger(__name__)


class VendorInfo(models.Model):
    _name = "vendor.info"
    _description = "Vendor Info"

    name = fields.Char(string="Name", required=True, index=True)
    supplier_id = fields.Many2one("res.partner", string="Supplier", index=True)
    currency_id = fields.Many2one(
        "res.currency", string="Currency", index=True, default=lambda self: self.env.company.currency_id
    )
    sequence_id = fields.Many2one("ir.sequence", string="Code Sequence")
    purchase_delay = fields.Integer(default=2)
    type_code = fields.Selection([("none", "None"), ("sequence", "Sequence"), ("code", "Code")], default="none")
    category_id = fields.Many2one("product.category", string="Product Category")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)

    price_base = fields.Selection(
        [("list_price", "List Price"), ("purchase_price", "Purchase Price")],
        "Based on",
        default="list_price",
        required=True,
        help="Base price for computation.\n"
        "Sales Price: The base price will be the List Price.\n"
        "Cost Price : The base price will be the Purchase Price.\n",
    )
    price_surcharge = fields.Float(
        "Price Surcharge",
        digits="Product Price",
        help="Specify the fixed amount to add or subtract(if negative) to the amount calculated with the discount.",
    )
    price_discount = fields.Float(
        "Price Discount", default=0, digits=(16, 2), help="You can apply a mark-up by setting a negative discount."
    )
    rule_tip = fields.Char(compute="_compute_rule_tip")

    source_url = fields.Char(string="Source URL")
    token_access = fields.Char(string="Token Access")

    @api.depends_context("lang")
    @api.depends("price_discount", "price_surcharge", "price_base")
    def _compute_rule_tip(self):
        base_selection_vals = {elem[0]: elem[1] for elem in self._fields["price_base"]._description_selection(self.env)}
        self.rule_tip = False
        for item in self:
            base_amount = 100
            discount_factor = (100 - item.price_discount) / 100
            discounted_price = base_amount * discount_factor
            currency_id = item.currency_id or item.company_id.currency_id
            surcharge = tools.format_amount(item.env, item.price_surcharge, currency_id)
            item.rule_tip = _(
                "%(base)s with a %(discount)s %% discount and %(surcharge)s extra fee\n"
                "Example: %(amount)s * %(discount_charge)s + %(price_surcharge)s → %(total_amount)s",
                base=base_selection_vals[item.price_base],
                discount=item.price_discount,
                surcharge=surcharge,
                amount=tools.format_amount(item.env, 100, currency_id),
                discount_charge=discount_factor,
                price_surcharge=surcharge,
                total_amount=tools.format_amount(item.env, discounted_price + item.price_surcharge, currency_id),
            )

    def _compute_price(self, price, price_uom):
        self.ensure_one()
        price = (price - (price * (self.price_discount / 100))) or 0.0
        if self.price_surcharge:
            price += self.price_surcharge
        return price

    @api.onchange("supplier_id")
    def onchange_supplier_id(self):
        if self.supplier_id:
            self.currency_id = self.supplier_id.property_purchase_currency_id
            self.name = self.supplier_id.name

    def load_from_file(self):
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_vendor_products.product_template_action")
        return action

    def unlink_product(self):
        self.env["vendor.product"].search([("supplier_id", "=", self.supplier_id.id)]).unlink()
