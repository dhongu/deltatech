# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def explode(self, product, quantity, picking_type=False, never_attribute_values=False):
        """Override of mrp to compute component quantities from a formula.

        The body is copied from mrp/models/mrp_bom.py; the only functional difference is that
        the quantity of a component is taken from _get_formula_quantity instead of the stored
        product_qty. The formula context is built from the attribute values of the exploded
        product and refined with the ones of the intermediate product on nested bills.
        """
        if not self.bom_line_ids.filtered("qty_formula"):
            return super().explode(
                product, quantity, picking_type=picking_type, never_attribute_values=never_attribute_values
            )

        self = self.with_context(bom_cost_share_cache=self.env.context.get("bom_cost_share_cache") or {})  # noqa: PLW0642
        defaults = self.env["product.attribute"]._get_formula_defaults()
        root_attr, root_num = product._get_formula_values(never_attribute_values, defaults=defaults)
        formula_cache = {product: (root_attr, root_num)}

        def get_formula_values(current_product):
            if current_product not in formula_cache:
                # The root configuration stays available on nested bills, where the intermediate
                # product usually carries no attribute of its own. Only the values the current
                # product really carries override it.
                own_attr, own_num = current_product._get_own_formula_values(never_attribute_values)
                formula_cache[current_product] = (dict(root_attr, **own_attr), dict(root_num, **own_num))
            return formula_cache[current_product]

        product_ids = set()
        product_boms = {}

        def update_product_boms():
            products = self.env["product.product"].browse(product_ids)
            product_boms.update(
                self._bom_find(
                    products,
                    picking_type=picking_type or self.picking_type_id,
                    company_id=self.company_id.id,
                    bom_type="phantom",
                )
            )
            for product_id in products:
                product_boms.setdefault(product_id, self.env["mrp.bom"])

        boms_done = [(self, self.env["mrp.bom.line"]._prepare_bom_done_values(quantity, product, quantity, []))]
        lines_done = []

        bom_lines = []
        for bom_line in self.bom_line_ids:
            bom_lines.append((bom_line, product, quantity, False))
            product_ids.add(bom_line.product_id.id)
        update_product_boms()
        product_ids.clear()
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            if current_line._skip_bom_line(current_product, never_attribute_values):
                continue

            attr, num = get_formula_values(current_product)
            line_quantity = current_qty * current_line._get_formula_quantity(attr, num)
            if current_line.product_id not in product_boms:
                update_product_boms()
                product_ids.clear()
            bom = product_boms.get(current_line.product_id)
            if bom:
                converted_line_quantity = current_line.product_uom_id._compute_quantity(
                    line_quantity / bom.product_qty, bom.product_uom_id, round=False
                )
                bom_lines = [
                    (line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids
                ] + bom_lines
                for bom_line in bom.bom_line_ids:
                    if bom_line.product_id not in product_boms:
                        product_ids.add(bom_line.product_id.id)
                boms_done.append(
                    (
                        bom,
                        current_line._prepare_bom_done_values(
                            converted_line_quantity, current_product, quantity, boms_done
                        ),
                    )
                )
            else:
                # We round up here because the user expects that if he has to consume a little more,
                # the whole UOM unit should be consumed.
                line_quantity = current_line.product_uom_id.round(line_quantity, rounding_method="UP")
                lines_done.append(
                    (
                        current_line,
                        current_line._prepare_line_done_values(
                            line_quantity, current_product, quantity, parent_line, boms_done
                        ),
                    )
                )

        lines_done = self._round_last_line_done(lines_done)
        return boms_done, lines_done


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    qty_formula = fields.Char(
        string="Quantity Formula",
        help="Python expression returning the quantity to consume. Two dictionaries are available: "
        "attr, mapping an attribute code to the code of the selected value, and num, mapping an "
        "attribute code to its numeric value. The quantity of this line is available as qty. "
        "Leave empty to use the quantity as it is.",
    )

    def _get_formula_eval_context(self, attr, num):
        self.ensure_one()
        return {
            "attr": attr,
            "num": num,
            "qty": self.product_qty,
            "ceil": math.ceil,
            "floor": math.floor,
        }

    def _get_formula_quantity(self, attr, num):
        """Return the quantity of this line for a given attribute configuration."""
        self.ensure_one()
        if not self.qty_formula:
            return self.product_qty
        try:
            result = safe_eval(self.qty_formula, self._get_formula_eval_context(attr, num))
        except KeyError as err:
            raise ValidationError(
                self.env._(
                    "The quantity formula of the component %(product)s refers to the unknown attribute code %(code)s.",
                    product=self.product_id.display_name,
                    code=err.args[0] if err.args else "",
                )
            ) from err
        except Exception as err:
            raise ValidationError(
                self.env._(
                    "The quantity formula of the component %(product)s could not be evaluated: %(error)s",
                    product=self.product_id.display_name,
                    error=err,
                )
            ) from err
        if not isinstance(result, int | float) or isinstance(result, bool):
            raise ValidationError(
                self.env._(
                    "The quantity formula of the component %(product)s must return a number, but it "
                    "returned %(result)s.",
                    product=self.product_id.display_name,
                    result=result,
                )
            )
        if result < 0:
            raise ValidationError(
                self.env._(
                    "The quantity formula of the component %(product)s returned the negative quantity %(result)s.",
                    product=self.product_id.display_name,
                    result=result,
                )
            )
        return float(result)

    def _get_formula_sample_values(self):
        """Build a plausible attribute configuration to smoke test a formula on save.

        Every attribute code known to the database is present, because a bill of material of a
        semi-finished product legitimately reads a characteristic of the root product. Only a
        code that exists nowhere is reported, which is the typo the check is there to catch.
        """
        self.ensure_one()
        attr, num = self.env["product.attribute"]._get_formula_defaults()
        for line in self.bom_id.product_tmpl_id.valid_product_template_attribute_line_ids:
            attribute_code = line.attribute_id.code
            value = line.product_template_value_ids[:1]
            if not attribute_code or not value:
                continue
            attr[attribute_code] = value.product_attribute_value_id.code or False
            num[attribute_code] = value.product_attribute_value_id.numeric_value
        return attr, num

    @api.constrains("qty_formula")
    def _check_qty_formula(self):
        for line in self.filtered("qty_formula"):
            attr, num = line._get_formula_sample_values()
            line._get_formula_quantity(attr, num)
