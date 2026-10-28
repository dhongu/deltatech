# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from collections import defaultdict
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError

QUARTERS = [("1", "Q1"), ("2", "Q2"), ("3", "Q3"), ("4", "Q4")]


class PurchaseTargetLine(models.Model):
    _name = "purchase.target.line"
    _description = "Purchase Target Line"
    _order = "year desc, manufacturer_id, quarter, public_categ_id NULLS FIRST, id"
    _check_company_auto = True

    # the sales come from the sale margin report (cost and profit): same rights as the report
    SALE_GROUPS = "deltatech_sale_margin.group_sale_margin,sales_team.group_sale_manager"

    target_id = fields.Many2one(
        "purchase.target", string="Purchase Target", required=True, ondelete="cascade", index=True
    )
    manufacturer_id = fields.Many2one(related="target_id.manufacturer_id", store=True)
    year = fields.Integer(related="target_id.year", store=True)
    company_id = fields.Many2one(related="target_id.company_id", store=True)
    currency_id = fields.Many2one(related="target_id.currency_id")
    target_type = fields.Selection(related="target_id.target_type")
    quarter = fields.Selection(QUARTERS, required=True, default="1")
    public_categ_id = fields.Many2one(
        "product.public.category",
        string="Category",
        help="eCommerce category of the products. Empty: the overall target of the manufacturer.",
    )
    # summing targets of different quarters and categories means nothing
    target_value = fields.Float(string="Target", aggregator=None)

    # the achieved figures are read live from the posted invoices, they are not stored
    target_ytd = fields.Float(string="Target YTD", compute="_compute_achieved")
    purchase_amount = fields.Monetary(string="Purchased", compute="_compute_achieved")
    purchase_qty = fields.Float(string="Purchased Qty", compute="_compute_achieved")
    purchase_ytd = fields.Float(string="Purchased YTD", compute="_compute_achieved")
    achieved_pct = fields.Float(string="Achieved %", compute="_compute_achieved")
    remaining = fields.Float(compute="_compute_achieved", help="Target YTD minus purchased YTD")
    sale_amount = fields.Monetary(string="Sold", compute="_compute_achieved", groups=SALE_GROUPS)
    sale_qty = fields.Float(string="Sold Qty", compute="_compute_achieved", groups=SALE_GROUPS)
    sale_ytd = fields.Float(string="Sold YTD", compute="_compute_achieved", groups=SALE_GROUPS)

    @api.constrains("target_id", "quarter", "public_categ_id")
    def _check_unique_quarter_categ(self):
        for line in self:
            duplicates = line.target_id.line_ids.filtered(
                lambda other, line=line: other != line
                and other.quarter == line.quarter
                and other.public_categ_id == line.public_categ_id
            )
            if duplicates:
                raise ValidationError(self.env._("The category already has a target in quarter Q%s.", line.quarter))

    def _product_domain(self, path="product_id"):
        self.ensure_one()
        domain = [(f"{path}.manufacturer_id", "=", self.manufacturer_id.id)]
        if self.public_categ_id:
            domain.append((f"{path}.public_categ_ids", "child_of", self.public_categ_id.id))
        return domain

    def _year_domain(self):
        self.ensure_one()
        return [("date", ">=", date(self.year, 1, 1)), ("date", "<=", date(self.year, 12, 31))]

    def _purchase_domain(self):
        self.ensure_one()
        return [
            ("parent_state", "=", "posted"),
            ("display_type", "=", "product"),
            ("move_id.move_type", "in", ("in_invoice", "in_refund")),
            ("move_id.commercial_partner_id", "in", self.target_id.partner_ids.ids),
            ("company_id", "=", self.company_id.id),
            *self._year_domain(),
            *self._product_domain(),
        ]

    def _sale_domain(self):
        self.ensure_one()
        return [
            ("company_id", "=", self.company_id.id),
            *self._year_domain(),
            *self._product_domain(),
        ]

    def _quarter_domain(self):
        self.ensure_one()
        quarter = int(self.quarter)
        date_from = date(self.year, 3 * quarter - 2, 1)
        date_to = date(self.year + 1, 1, 1) if quarter == 4 else date(self.year, 3 * quarter + 1, 1)
        return [("date", ">=", date_from), ("date", "<", date_to)]

    def _read_purchases(self):
        """Purchases of the year per quarter: {quarter: (amount, qty)}, credit notes deducted."""
        result = defaultdict(lambda: [0.0, 0.0])
        # sudo: the purchase users follow the targets without accounting rights. They get only
        # the totals per quarter of the target's own company and vendors, the volume they
        # already see on the purchase orders; the bill lines (drill-down) need accounting rights.
        lines = self.env["account.move.line"].sudo()
        for move_type, sign in (("in_invoice", 1), ("in_refund", -1)):
            domain = [*self._purchase_domain(), ("move_id.move_type", "=", move_type)]
            # the quantity is in the unit of the bill line (a box, a dozen): grouped per unit and
            # product, to convert it to the unit of the product
            groups = lines._read_group(
                domain, ["date:quarter_number", "product_uom_id", "product_id"], ["balance:sum", "quantity:sum"]
            )
            for quarter, line_uom, product, balance, quantity in groups:
                if line_uom and line_uom != product.uom_id:
                    quantity = line_uom._compute_quantity(quantity, product.uom_id, round=False)
                # the balance of a credit note is already negative, only the quantity is unsigned
                result[quarter][0] += balance
                result[quarter][1] += sign * quantity
        return result

    def _read_sales(self):
        """Sales of the year per quarter: {quarter: (amount, qty)}, from the sale margin report."""
        result = defaultdict(lambda: [0.0, 0.0])
        if not self.env.user.has_groups(self.SALE_GROUPS):
            return result
        groups = self.env["sale.margin.report"]._read_group(
            self._sale_domain(), ["date:quarter_number"], ["sale_val:sum", "product_uom_qty:sum"]
        )
        for quarter, amount, qty in groups:
            result[quarter][0] += amount
            result[quarter][1] += qty
        return result

    @api.depends(
        "target_value",
        "quarter",
        "public_categ_id",
        "year",
        "target_type",
        "company_id",
        "manufacturer_id",
        "target_id.partner_ids",
        "target_id.line_ids",
    )
    def _compute_achieved(self):
        # the four quarters of a category share the same figures: read them once per year
        cache = {}
        for line in self:
            if not line.target_id or not line.year:
                line.update(
                    {
                        "target_ytd": 0.0,
                        "purchase_amount": 0.0,
                        "purchase_qty": 0.0,
                        "purchase_ytd": 0.0,
                        "achieved_pct": 0.0,
                        "remaining": 0.0,
                        "sale_amount": 0.0,
                        "sale_qty": 0.0,
                        "sale_ytd": 0.0,
                    }
                )
                continue
            key = (line.target_id.id, line.public_categ_id.id)
            if key not in cache:
                cache[key] = (line._read_purchases(), line._read_sales())
            purchases, sales = cache[key]
            quarter = int(line.quarter)
            measure = 1 if line.target_type == "qty" else 0
            target_ytd = sum(
                sibling.target_value
                for sibling in line.target_id.line_ids
                if sibling.public_categ_id == line.public_categ_id and int(sibling.quarter) <= quarter
            )
            purchase_ytd = sum(values[measure] for q, values in purchases.items() if q <= quarter)
            line.update(
                {
                    "target_ytd": target_ytd,
                    "purchase_amount": purchases[quarter][0],
                    "purchase_qty": purchases[quarter][1],
                    "purchase_ytd": purchase_ytd,
                    "achieved_pct": 100.0 * purchase_ytd / target_ytd if target_ytd else 0.0,
                    "remaining": target_ytd - purchase_ytd,
                    "sale_amount": sales[quarter][0],
                    "sale_qty": sales[quarter][1],
                    "sale_ytd": sum(values[measure] for q, values in sales.items() if q <= quarter),
                }
            )

    def action_view_purchases(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Purchases - %s", self.display_name),
            "res_model": "account.move.line",
            "view_mode": "list",
            "views": [(self.env.ref("deltatech_purchase_target.view_move_line_purchase_target_list").id, "list")],
            "search_view_id": self.env.ref("deltatech_purchase_target.view_move_line_purchase_target_search").id,
            "domain": [*self._purchase_domain(), *self._quarter_domain()],
            "context": {"create": False},
        }

    def action_view_sales(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("deltatech_sale_margin.action_sale_margin_report")
        action["domain"] = [*self._sale_domain(), *self._quarter_domain()]
        action["context"] = {}
        action["view_mode"] = "list,pivot"
        action["views"] = [(False, "list"), (False, "pivot")]
        return action

    @api.depends("target_id", "quarter", "public_categ_id")
    def _compute_display_name(self):
        for line in self:
            quarters = dict(line._fields["quarter"]._description_selection(line.env))
            parts = [line.target_id.display_name, quarters.get(line.quarter)]
            if line.public_categ_id:
                parts.append(line.public_categ_id.display_name)
            line.display_name = " / ".join(p for p in parts if p)
