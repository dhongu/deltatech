# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import Command, api, fields, models
from odoo.exceptions import UserError

# in progress: de facut legatura cu listele de preturi


class ProductPriceChange(models.Model):
    _name = "product.price.change"
    _description = "Product Price Change"
    _inherit = ["mail.thread"]
    _order = "date desc"

    name = fields.Char(
        "Number",
        size=64,
        index=True,
        readonly=True,
        default="/",
    )

    date = fields.Date(
        "Date",
        required=True,
        index=True,
        default=fields.Date.today,
    )

    partner_id = fields.Many2one(related="warehouse_id.partner_id", string="Owner Address", readonly=True)

    state = fields.Selection([("draft", "Draft"), ("done", "Done")], "Status", default="draft")

    line_ids = fields.One2many(
        "product.price.change.line",
        "price_change_id",
        "Price History Lines",
        copy=True,
    )

    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    location_id = fields.Many2one("stock.location", "Location")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    type = fields.Selection(
        [
            ("product", "In product"),
            ("pricelist", "In pricelist"),
            ("log", "From price changes"),
        ]
    )
    default_pricelist_id = fields.Many2one("product.pricelist")
    use_product_template = fields.Boolean()

    parent_id = fields.Many2one(
        "product.price.change",
        "Parent Product Price Change",
        index=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        "product.price.change",
        "parent_id",
        string="Child Product Price Change",
        readonly=True,
    )

    old_amount = fields.Monetary(compute="_compute_amount_all", string="Old Amount")
    new_amount = fields.Monetary(compute="_compute_amount_all", string="New Amount")
    diff_amount = fields.Monetary(compute="_compute_amount_all", string="Difference Amount")

    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")

    @api.depends("line_ids.old_price", "line_ids.new_price", "line_ids.quantity")
    def _compute_amount_all(self):
        for change in self:
            old_amount = 0
            new_amount = 0

            for line in change.line_ids:
                old_amount += line.old_price * line.quantity
                new_amount += line.new_price * line.quantity

            change.old_amount = old_amount
            change.new_amount = new_amount
            change.diff_amount = new_amount - old_amount

    @api.onchange("type")
    def _onchange_type(self):
        if self.type == "log":
            self.use_product_template = True

    def action_load_price_changes(self):
        """Bring in the list price changes logged up to the document date and not taken by another document"""
        Log = self.env["product.price.change.log"]
        for change in self:
            if change.state != "draft" or change.type != "log":
                continue
            domain = [
                ("price_change_id", "=", False),
                ("date", "<=", change.date),
                ("company_id", "in", [change.company_id.id, False]),
            ]
            logs = Log.search(domain, order="date, id")
            if not logs:
                continue
            change.write(
                {
                    "use_product_template": True,
                    "line_ids": [
                        Command.create(
                            {
                                "log_id": log.id,
                                "product_template_id": log.product_tmpl_id.id,
                                "old_price": log.old_price,
                                "new_price": log.new_price,
                            }
                        )
                        for log in logs
                    ],
                }
            )
        return True

    def action_confirm(self):
        for change in self:
            if change.name == "/":
                change.name = self.env["ir.sequence"].next_by_code("price.change") or "/"
        self.write({"state": "done"})
        # aici se actualizeaza si preturile din produse

        for change in self:
            if not change.location_id and change.type in ("product", "log"):
                locations = self.env["stock.location"].search([("usage", "=", "internal")])

                for location in locations:
                    new_lines = []
                    warehouse = location.warehouse_id
                    for line in change.line_ids:
                        if line.product_id:
                            domain = [("product_id", "=", line.product_id.id)]
                        else:
                            domain = [("product_id.product_tmpl_id", "=", line.product_template_id.id)]
                        quants = self.env["stock.quant"].search(domain + [("location_id", "=", location.id)])
                        available = sum(quants.mapped("quantity"))

                        if available != 0:
                            new_lines.append(
                                Command.create(
                                    {
                                        "product_id": line.product_id.id,
                                        "product_template_id": line.product_template_id.id,
                                        "old_price": line.old_price,
                                        "new_price": line.new_price,
                                    }
                                )
                            )

                    if new_lines:
                        self.create(
                            {
                                "name": change.name,
                                "date": change.date,
                                "type": change.type,
                                "use_product_template": change.use_product_template,
                                "parent_id": change.id,
                                "warehouse_id": warehouse.id,
                                "location_id": location.id,
                                "state": "done",
                                "line_ids": new_lines,
                            }
                        )
                        if warehouse.partner_id:
                            change.message_subscribe([warehouse.partner_id.id])
                        change.message_post(
                            body=self.env._("New Price Change"),
                            message_type="comment",
                            subtype_xmlid="mail.mt_comment",
                        )

        # the prices written by the document are not logged: the document is their record
        for change in self.filtered(lambda ch: ch.type == "product"):
            for line in change.line_ids:
                if line.product_id and not line.price_change_id.use_product_template:
                    line.product_id.with_context(ref=change.name, skip_price_change_log=True).write(
                        {"list_price": line.new_price}
                    )
                if line.product_template_id and line.price_change_id.use_product_template:
                    line.product_template_id.with_context(ref=change.name, skip_price_change_log=True).write(
                        {"list_price": line.new_price}
                    )
        for change in self.filtered(lambda ch: ch.type == "pricelist"):
            pricelist_lines = []
            for line in change.line_ids:
                if line.product_id and not line.price_change_id.use_product_template:
                    # delete lines with the same product variant if found
                    domain = [
                        ("pricelist_id", "=", line.pricelist_id.id),
                        ("product_id", "=", line.product_id.id),
                        ("date_start", "=", line.pricelist_date_start),
                        ("date_end", "=", line.pricelist_date_end),
                    ]
                    to_delete_lines = self.env["product.pricelist.item"].search(domain)
                    to_delete_lines.unlink()
                    price_list_vals = {
                        "applied_on": "0_product_variant",
                        "base": "list_price",
                        "compute_price": "fixed",
                        "pricelist_id": line.pricelist_id.id,
                        "fixed_price": line.new_price,
                        "product_id": line.product_id.id,
                        "date_start": line.pricelist_date_start,
                        "date_end": line.pricelist_date_end,
                    }
                    pricelist_lines.append(price_list_vals)
                if line.product_template_id and line.price_change_id.use_product_template:
                    # delete lines with the same product variant if found
                    domain = [
                        ("pricelist_id", "=", line.pricelist_id.id),
                        ("product_tmpl_id", "=", line.product_template_id.id),
                        ("date_start", "=", line.pricelist_date_start),
                        ("date_end", "=", line.pricelist_date_end),
                    ]
                    to_delete_lines = self.env["product.pricelist.item"].search(domain)
                    to_delete_lines.unlink()
                    price_list_vals = {
                        "applied_on": "1_product",
                        "base": "list_price",
                        "compute_price": "fixed",
                        "pricelist_id": line.pricelist_id.id,
                        "fixed_price": line.new_price,
                        "product_tmpl_id": line.product_template_id.id,
                        "date_start": line.pricelist_date_start,
                        "date_end": line.pricelist_date_end,
                    }
                    pricelist_lines.append(price_list_vals)
            self.env["product.pricelist.item"].create(pricelist_lines)
        return True

    def unlink(self):
        if not self.env.context.get("force_delete", False):
            for change in self:
                if change.state not in ["draft"]:
                    raise UserError(self.env._("Change Price document with status 'Done' cant't by deleted"))
        return super().unlink()


class ProductPriceChangeLine(models.Model):
    _name = "product.price.change.line"
    _description = "ProductPriceChangeLine"
    _rec_name = "product_id"

    price_change_id = fields.Many2one(
        "product.price.change", "Product Price Change", readonly=True, index=True, ondelete="cascade"
    )
    sequence = fields.Integer(
        "Sequence",
        help="Gives the sequence order when displaying a list of product with price changed.",
    )
    product_id = fields.Many2one("product.product", "Product")
    product_template_id = fields.Many2one("product.template")
    log_id = fields.Many2one("product.price.change.log", "Price Change Log", index=True, ondelete="cascade")
    change_date = fields.Date(related="log_id.date", string="Change Date")

    old_price = fields.Float("Old Sale Price", digits="Product Price")
    old_amount = fields.Monetary(
        compute="_compute_old_amount",
        string="Old Amount",
        readonly=True,
        store=True,
    )

    new_price = fields.Float("New Sale Price", required=True, digits="Product Price")
    new_amount = fields.Monetary(
        compute="_compute_new_amount",
        string="New Amount",
        readonly=True,
        store=True,
    )

    diff_amount = fields.Monetary(
        compute="_compute_diff_amount",
        string="Difference Amount",
        readonly=True,
        store=True,
    )

    old_price_incl = fields.Float("Old Price incl. Taxes", compute="_compute_price_incl", digits="Product Price")
    new_price_incl = fields.Float("New Price incl. Taxes", compute="_compute_price_incl", digits="Product Price")

    quantity = fields.Float(
        "Quantity",
        digits="Product Unit",
        readonly=True,
        compute="_compute_quantity",
        store=True,
    )

    currency_id = fields.Many2one("res.currency", related="price_change_id.currency_id")
    pricelist_id = fields.Many2one("product.pricelist")
    pricelist_date_start = fields.Datetime(string="Start Date")
    pricelist_date_end = fields.Datetime(string="End Date")

    @api.depends("old_price", "quantity")
    def _compute_old_amount(self):
        for line in self:
            line.old_amount = line.old_price * line.quantity

    @api.depends("new_price", "quantity")
    def _compute_new_amount(self):
        for line in self:
            line.new_amount = line.new_price * line.quantity

    @api.depends("old_price", "new_price", "quantity")
    def _compute_diff_amount(self):
        for line in self:
            line.diff_amount = line.new_price * line.quantity - line.old_price * line.quantity

    @api.depends("old_price", "new_price", "product_id", "product_template_id")
    def _compute_price_incl(self):
        for line in self:
            product = line.product_id or line.product_template_id
            company = line.price_change_id.company_id or self.env.company
            taxes = product.taxes_id.filtered(lambda t, c=company: t.company_id in c.parent_ids)
            currency = company.currency_id
            line.old_price_incl = taxes.compute_all(line.old_price, currency, product=product)["total_included"]
            line.new_price_incl = taxes.compute_all(line.new_price, currency, product=product)["total_included"]

    @api.depends("product_id", "product_template_id")
    def _compute_quantity(self):
        for line in self:
            product = line.product_id or line.product_template_id
            line.quantity = product.with_context(
                warehouse_id=line.price_change_id.warehouse_id.id,
                location=line.price_change_id.location_id.id,
            ).qty_available

    @api.onchange("product_id", "pricelist_id", "product_template_id")
    def onchange_product_id(self):
        if self.log_id:
            return
        if (
            self.price_change_id.default_pricelist_id
            and not self.pricelist_id
            and (self.product_id or self.product_template_id)
        ):
            self.pricelist_id = self.price_change_id.default_pricelist_id

        if not self.price_change_id.use_product_template:
            product = self.product_id
            if not self.pricelist_id:
                self.old_price = product.list_price
            else:
                self.old_price = self.pricelist_id._get_product_price(product=self.product_id, quantity=1)
            self.new_price = self.old_price
        else:
            product_template = self.product_template_id
            if not self.pricelist_id:
                self.old_price = product_template.list_price
            else:
                self.old_price = self.pricelist_id._get_product_price(product=product_template, quantity=1)
            self.new_price = self.old_price
