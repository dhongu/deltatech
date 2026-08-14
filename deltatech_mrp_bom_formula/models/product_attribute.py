# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re
import unicodedata

from odoo import api, fields, models
from odoo.exceptions import ValidationError


def slugify_code(name):
    """Turn a human readable name into a technical identifier usable in a formula."""
    if not name:
        return False
    text = unicodedata.normalize("NFKD", name)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    if not text:
        return False
    if text[0].isdigit():
        text = "a_" + text
    return text


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    code = fields.Char(
        string="Formula Code",
        compute="_compute_code",
        store=True,
        readonly=False,
        help="Technical identifier used as key in the attribute dictionaries available "
        "in bill of material quantity formulas.",
    )

    @api.depends("name")
    def _compute_code(self):
        for attribute in self:
            if not attribute.code:
                attribute.code = attribute._get_unique_code(slugify_code(attribute.name))

    def _get_unique_code(self, code):
        """Append a numeric suffix when the generated code is already taken."""
        if not code:
            return False
        candidate = code
        index = 1
        while self.sudo().search_count([("code", "=", candidate), ("id", "not in", self.ids)], limit=1):
            index += 1
            candidate = f"{code}_{index}"
        return candidate

    @api.model
    def _get_formula_defaults(self):
        """Return the neutral formula dictionaries, holding every attribute code in the database.

        A formula may legitimately mention an attribute the exploded product does not carry, so
        an unset characteristic evaluates to False in attr and to 0.0 in num. A code that matches
        no attribute at all stays absent, and raises when the formula reads it.
        """
        codes = [attribute["code"] for attribute in self.sudo().search_read([("code", "!=", False)], ["code"])]
        return dict.fromkeys(codes, False), dict.fromkeys(codes, 0.0)

    @api.constrains("code")
    def _check_code_unique(self):
        for attribute in self:
            if not attribute.code:
                continue
            duplicate = self.sudo().search([("code", "=", attribute.code), ("id", "!=", attribute.id)], limit=1)
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "The formula code %(code)s is already used by the attribute %(name)s. "
                        "Formula codes must be unique.",
                        code=attribute.code,
                        name=duplicate.name,
                    )
                )


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    code = fields.Char(
        string="Formula Code",
        compute="_compute_code",
        store=True,
        readonly=False,
        help="Value returned by the attr dictionary in bill of material quantity formulas.",
    )
    numeric_value = fields.Float(
        string="Numeric Value",
        digits="Product Unit of Measure",
        help="Value returned by the num dictionary in bill of material quantity formulas. "
        "Use it for attributes that carry a measurable characteristic, such as a length.",
    )

    @api.depends("name")
    def _compute_code(self):
        for value in self:
            if not value.code:
                value.code = slugify_code(value.name)


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    code = fields.Char(related="product_attribute_value_id.code")
    numeric_value = fields.Float(related="product_attribute_value_id.numeric_value")
    attribute_code = fields.Char(string="Attribute Formula Code", related="attribute_id.code")
