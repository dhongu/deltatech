# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError


class PricelistFormulaMixin(models.AbstractModel):
    """Price computation fields of a pricelist rule, shared by the bulk wizards.

    The fields mirror ``product.pricelist.item``; ``_get_formula_vals`` returns
    them cleaned the same way the standard ``_onchange_compute_price`` does, so
    the values of the other price types are not left behind on the rules.
    """

    _name = "pricelist.formula.mixin"
    _description = "Pricelist Rule Formula"

    compute_price = fields.Selection(
        selection=[
            ("fixed", "Fixed Price"),
            ("percentage", "Discount"),
            ("formula", "Formula"),
        ],
        string="Price Type",
        default="fixed",
        required=True,
    )
    fixed_price = fields.Float(digits="Product Price")
    percent_price = fields.Float(
        string="Discount (%)",
        help="You can apply a mark-up by setting a negative discount.",
    )
    base = fields.Selection(
        selection=[
            ("list_price", "Sales Price"),
            ("standard_price", "Cost"),
            ("pricelist", "Other Pricelist"),
        ],
        string="Based on",
        default="list_price",
        required=True,
    )
    base_pricelist_id = fields.Many2one("product.pricelist", string="Other Pricelist")
    price_discount = fields.Float(
        string="Formula Discount (%)",
        digits=(16, 2),
        help="You can apply a mark-up by setting a negative discount.",
    )
    price_markup = fields.Float(string="Markup (%)", digits=(16, 2), help="Mark-up applied on the cost.")
    price_round = fields.Float(
        string="Round off to",
        digits="Product Price",
        help="Sets the price so that it is a multiple of this value. To have prices that end in 9.99, "
        "round off to 10.00 and set an extra fee of -0.01.",
    )
    price_surcharge = fields.Float(string="Extra Fee", digits="Product Price")
    price_min_margin = fields.Float(string="Min. Margin", digits="Product Price")
    price_max_margin = fields.Float(string="Max. Margin", digits="Product Price")

    @api.onchange("compute_price")
    def _onchange_formula_compute_price(self):
        self.base_pricelist_id = False
        if self.compute_price != "formula":
            self.base = "list_price"

    @api.onchange("base")
    def _onchange_formula_base(self):
        self.price_discount = 0.0
        self.price_markup = 0.0

    def _check_base_pricelist(self, vals, pricelists):
        """Refuse a rule based on its own pricelist, whatever the price type.

        ``vals`` are the values written on the rules: the Discount type on another pricelist
        also sets ``base_pricelist_id``, not only the Formula type.
        """
        if vals.get("base_pricelist_id") and vals["base_pricelist_id"] in pricelists.ids:
            raise UserError(self.env._("A rule cannot be based on its own pricelist."))

    def _get_formula_vals(self):
        """Return the values of the price computation, ready to write on the rules."""
        self.ensure_one()
        vals = {
            "compute_price": self.compute_price,
            "fixed_price": 0.0,
            "percent_price": 0.0,
            "base": "list_price",
            "base_pricelist_id": False,
            "price_discount": 0.0,
            "price_surcharge": 0.0,
            "price_round": 0.0,
            "price_min_margin": 0.0,
            "price_max_margin": 0.0,
        }
        if self.compute_price == "fixed":
            vals["fixed_price"] = self.fixed_price
        elif self.compute_price == "percentage":
            vals["percent_price"] = self.percent_price
            if self.base_pricelist_id:
                vals.update(base="pricelist", base_pricelist_id=self.base_pricelist_id.id)
        else:
            if self.price_round < 0.0:
                raise UserError(self.env._("The rounding must be strictly positive."))
            if self.base == "pricelist" and not self.base_pricelist_id:
                raise UserError(self.env._("Set the other pricelist the formula is based on."))
            discount = -self.price_markup if self.base == "standard_price" else self.price_discount
            vals.update(
                base=self.base,
                base_pricelist_id=self.base_pricelist_id.id if self.base == "pricelist" else False,
                price_discount=discount,
                price_surcharge=self.price_surcharge,
                price_round=self.price_round,
                price_min_margin=self.price_min_margin,
                price_max_margin=self.price_max_margin,
            )
        return vals
