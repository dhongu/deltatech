# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    price_warning_message = fields.Char(compute="_compute_price_warning_message")

    can_change_price = fields.Boolean(compute="_compute_can_change_price")

    @api.depends("user_id")
    def _compute_can_change_price(self):
        self.can_change_price = not self.env.user.has_group("deltatech_sale_margin.group_sale_no_change_price")

    @api.depends(
        "state",
        "order_line.margin_below_limit",
        "company_id.sale_margin_check_mode",
    )
    def _compute_price_warning_message(self):
        self.price_warning_message = False
        for order in self.filtered(lambda o: o.state in ["draft", "sent"]):
            company = order.company_id or self.env.company
            if company.sale_margin_check_mode == "off":
                continue
            warning_message = ""
            for line in order.order_line.filtered("margin_below_limit"):
                warning_message += self.env._(
                    "The unit price of product %s is lower than the purchase price. The margin is negative."
                ) % (line.product_id.display_name)
            if warning_message and company.sale_margin_check_mode == "warn":
                # in "warn" mode nothing is blocked, so the banner has to say so
                # explicitly - otherwise the seller stops at it waiting for a
                # permission that will never be needed
                warning_message += self.env._(" The order can still be confirmed.")
            if warning_message:
                order.price_warning_message = warning_message

    # la validare se verifica pretul de vanzare
    def action_confirm(self):
        res = super().action_confirm()
        if self.env.context.get("ignore_price_check", False):
            return res
        # daca comanda se face in website se ignora verificarea pretului de cost pentru a face unele promotii
        if self.env.context.get("website_id", False):
            return res
        for order in self.filtered(lambda o: (o.company_id or self.env.company).sale_margin_check_mode == "warn"):
            order._post_margin_warning()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", "0"))
        if check_on_validate:
            for order in self:
                for line in order.order_line:
                    line.with_context(call_from_action_confirm=True).check_sale_price()
        return res

    def _post_margin_warning(self):
        """Log the below-cost decision once, when the order is confirmed.

        In "warn" mode `check_sale_price` stays silent on purpose: it runs on
        every `write` of a line, so posting from there filled the chatter with
        one message per keystroke on the price and nobody read it any more.
        """
        self.ensure_one()
        lines = self.order_line.filtered("margin_below_limit")
        if not lines:
            return
        details = ""
        for line in lines:
            detail = self.env._(
                "%(product)s - unit price %(price)s %(currency)s, margin %(margin)s%%",
                product=line.product_id.display_name,
                price=round(line.price_reduce_taxexcl, 2),
                currency=line.currency_id.name or "",
                margin=round(line.margin_percent * 100, 2),
            )
            details += f"<li>{detail}</li>"
        self.message_post(
            body=self.env._(
                "<p><b>Sold below cost - confirmed.</b> The lines below are under "
                "the configured margin limit. The order was NOT blocked; this note "
                "keeps a trace of the decision.</p><ul>%s</ul>",
                details,
            )
        )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    margin_below_limit = fields.Boolean(
        string="Below cost",
        compute="_compute_margin_below_limit",
        help="The margin of this line is under the configured margin limit.",
    )

    # Not stored: it depends on a company setting and on a system parameter, and
    # storing it would mean recomputing every historical line whenever either of
    # them changes. It is only ever needed on screen.
    #
    # Deliberately a separate compute from the native `margin` / `margin_percent`
    # rather than a groups-restricted field of its own: `margin_below_limit` must
    # stay readable by sellers who are NOT allowed to see the cost, which is the
    # whole point of a warning. A field carrying the figure would leak it.
    @api.depends(
        "price_reduce_taxexcl",
        "purchase_price",
        "product_id",
        "product_uom_id",
        "company_id.sale_margin_check_mode",
    )
    def _compute_margin_below_limit(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        margin_limit = safe_eval(get_param("sale.margin_limit", "0"))
        for line in self:
            margin = line._margin_for_check()
            line.margin_below_limit = (
                line._margin_check_mode() != "off" and margin is not None and margin < margin_limit
            )

    def _margin_check_mode(self):
        """Reaction mode of the line's company, resolved defensively.

        During an onchange the line may not have a company yet (`company_id` is
        related to the order). Falling through to a missing company would return
        a falsy mode, which reads as "not block" everywhere below and would
        silently disable the check for every existing customer - a regression
        nobody would notice until a sale below cost went through.
        """
        self.ensure_one()
        company = self.company_id or self.order_id.company_id or self.env.company
        return company.sale_margin_check_mode

    def _margin_for_check(self):
        """Margin percentage of the line, or None when it cannot be compared.

        None means "stay silent": no product, a service, a delivery line, no
        cost at all (the purchase price was never filled in), no price, or units
        that are not comparable.
        """
        self.ensure_one()
        if self.display_type or not self.product_id:
            return None
        if self.product_type == "service" or self.is_delivery:
            return None
        cost = self.purchase_price
        price = self.price_reduce_taxexcl
        if cost <= 0 or price <= 0:
            return None
        if not self._margin_uom_comparable():
            return None
        return (price - cost) / price * 100

    def _margin_uom_comparable(self):
        """Are the cost and the price expressed in the same unit?

        `purchase_price` is brought into the line unit by `sale_margin` /
        `sale_stock_margin` through `product_id.uom_id._compute_price(...)`. In
        Odoo 19 that multiplies by the ABSOLUTE factors without checking the
        family - the unit category is gone and the root of the kilogram
        hierarchy is the gram - so converting a cost per Unit into a price per kg
        returns a value 1000 times too high.

        Left unchecked, a product whose `uom_id` is wrong would report EVERY line
        as below cost, and the warning would be dismissed as noise from day one.
        """
        self.ensure_one()
        line_uom = self.product_uom_id or self.product_id.uom_id
        base_uom = self.product_id.uom_id
        if not line_uom or not base_uom:
            return False
        return line_uom._dt_root_uom() == base_uom._dt_root_uom()

    # def get_price_unit_w_taxes(self):
    #     # check if price_unit is with taxes
    #     if not self.display_type:
    #         with_taxes = False
    #         for tax in self.tax_id:
    #             if tax.price_include:
    #                 with_taxes = True
    #         if with_taxes:
    #             if self.product_uom_qty != 0.0:
    #                 price_unit = self.price_unit - self.price_tax / self.product_uom_qty
    #             else:
    #                 price_unit = self.price_unit - self.price_tax
    #         else:
    #             price_unit = self.price_unit
    #         return price_unit
    #     else:
    #         return False

    def change_price_or_product(self, res=None):
        #
        if not res:
            res = {}
        if not res.get("warning", False) and not self.env.context.get("website_id", False):
            # In "warn" mode the signal is the flagged line and the order banner,
            # which appear as soon as the seller leaves the price field. A modal
            # on top of that, on a business where selling below cost is routine,
            # ends up being dismissed reflexively without being read.
            if self._margin_check_mode() != "block":
                return res
            get_param = self.env["ir.config_parameter"].sudo().get_param
            check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", "0"))
            if check_on_validate:
                return res
            price_unit = self.price_reduce_taxexcl
            if price_unit and price_unit < self.purchase_price and self.purchase_price > 0:
                warning = {
                    "title": self.env._("Price Error!"),
                    "message": self.env._("Do not sell below the purchase price."),
                }
                res["warning"] = warning
        return res

    @api.onchange("product_id")
    def _onchange_product_id_warning(self):
        # res = super()._onchange_product_id_warning() or {}
        res = self.change_price_or_product()
        return res

    @api.onchange("price_unit")
    def price_unit_change(self):
        res = {}
        res = self.change_price_or_product(res)
        return res

    def write(self, vals):
        res = super().write(vals)
        get_param = self.env["ir.config_parameter"].sudo().get_param
        check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", "0"))
        if not check_on_validate:
            for line in self.filtered(lambda li: li._margin_check_mode() == "block"):
                line.check_sale_price()
        return res

    def check_sale_price(self):
        res = {}
        # daca in context este ignore_price_check atunci nu se verifica pretul
        if self.env.context.get("ignore_price_check", False):
            return res
        # "warn" and "off" never raise: the signal is `margin_below_limit` (the
        # flagged line and the order banner) plus a single chatter note posted by
        # `sale.order._post_margin_warning` when the order is confirmed. This
        # method runs on every `write` of a line, so warning from here would
        # either block routine work or flood the chatter.
        if self._margin_check_mode() != "block":
            return res
        # daca comanda se face in website se ignora verificarea pretului de cost pentru a face unele promotii
        if self.env.context.get("website_id", False):
            return res

        get_param = self.env["ir.config_parameter"].sudo().get_param
        margin_limit = safe_eval(get_param("sale.margin_limit", "0"))

        # verificare doar la validare
        check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", "0"))
        if check_on_validate and not self.env.context.get("call_from_action_confirm", False):
            return res

        check_price_website = safe_eval(get_param("sale.check_price_website", "False"))
        if check_price_website:
            # pentru comenzile din website nu se face verificarea
            domain = [("name", "=", "website_sale"), ("state", "=", "installed")]
            website_sale_module = self.env["ir.module.module"].sudo().search(domain)
            if website_sale_module:
                if self.order_id.website_id:
                    return res

        for line in self.filtered(lambda li: li.qty_to_deliver):
            if (
                line.display_type in ("line_section", "line_note")
                or line.product_type == "service"
                or line.product_uom_qty < 0
                or line.is_delivery
            ):
                continue

            #
            if line.product_id and line.price_unit == 0:
                # liniile generate de recompense de loialitate au preț 0 intenționat
                if hasattr(line, "reward_id") and line.reward_id:
                    continue
                if not self.env.user.has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                    raise UserError(self.env._("You can not sell %s without price.") % line.product_id.name)
                else:
                    message = self.env._("Sale %s without price.") % line.product_id.name
                    line.order_id.message_post(body=message)
            price_unit = line.price_reduce_taxexcl
            if price_unit:
                if price_unit < line.purchase_price:
                    if not self.env.user.has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                        raise UserError(
                            self.env._("You can not sell below the purchase price: %s.", line.product_id.name)
                        )
                    else:
                        message = self.env._("Sale %s under the purchase price.") % line.product_id.name
                        line.order_id.message_post(body=message)

                margin = (price_unit - line.purchase_price) / price_unit * 100
                if margin < margin_limit:
                    if not self.env.user.has_group("deltatech_sale_margin.group_sale_below_margin"):
                        raise UserError(self.env._("You can not sell below margin: %s") % line.product_id.name)
                    else:
                        message = self.env._("Sale %s below margin.") % line.product_id.name
                        line.order_id.message_post(body=message)
