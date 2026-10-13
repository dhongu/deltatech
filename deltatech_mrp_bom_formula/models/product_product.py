# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_own_formula_values(self, extra_attribute_values=None):
        """Return only the attribute values this variant actually carries.

        Kept apart from _get_formula_values because a caller that merges the configuration of
        several products must not overwrite a characteristic of one with the neutral value of
        another.

        :param extra_attribute_values: product.template.attribute.value records that are not
            carried by the variant itself, typically the no_variant values propagated to a
            manufacturing order.
        """
        self.ensure_one()
        attr = {}
        num = {}
        values = self.product_template_attribute_value_ids
        if extra_attribute_values:
            values |= extra_attribute_values
        for value in values:
            attribute_code = value.attribute_id.code
            if not attribute_code:
                continue
            attr[attribute_code] = value.product_attribute_value_id.code or False
            num[attribute_code] = value.product_attribute_value_id.numeric_value
        return attr, num

    def _get_formula_values(self, extra_attribute_values=None, defaults=None):
        """Return the attribute values of this variant as two formula dictionaries.

        Both dictionaries hold an entry for every attribute code defined in the database, so that
        a formula referring to an attribute the product does not carry gets a neutral value
        instead of an error. This is what makes a formula usable on a bill of material of a
        semi-finished product, where the characteristic belongs to the root product. Only a code
        that exists nowhere raises, which is the typo case.

        :param defaults: the neutral dictionaries returned by _get_formula_defaults, to be passed
            by a caller that explodes several products in a row.
        :return: a tuple (attr, num) where attr maps an attribute code to the code of its
            selected value and num maps an attribute code to its numeric value.
        """
        self.ensure_one()
        default_attr, default_num = defaults or self.env["product.attribute"]._get_formula_defaults()
        own_attr, own_num = self._get_own_formula_values(extra_attribute_values)
        return dict(default_attr, **own_attr), dict(default_num, **own_num)
