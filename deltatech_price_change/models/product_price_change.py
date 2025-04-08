# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
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
        # default=lambda self: self.env["ir.sequence"].next_by_code("price.change"),
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
        default=lambda self: self.env["res.company"]._company_default_get("product.price.change"),
    )
    type = fields.Selection([("product", "In product"), ("pricelist", "In pricelist")])
    default_pricelist_id = fields.Many2one("product.pricelist")
    use_product_template = fields.Boolean()

    # lot_stock_id = fields.related('warehouse_id', 'lot_stock_id',
    # type="many2one", relation="stock.location", readonly=True ),
    # address_id = fields.related('lot_stock_id', 'partner_id',
    # type="many2one", relation="res.partner", string="Address",readonly=True )

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

    def action_confirm(self):
        self.write({"state": "done"})
        # aici se actualizeaza si preturile din produse

        for change in self:
            if not change.location_id and change.type == "product":
                locations = self.env["stock.location"].search([("usage", "=", "internal")])

                for location in locations:
                    new_lines = []
                    warehouse = location.warehouse_id
                    for line in change.line_ids:
                        available = 0
                        quant_ids = self.env["stock.quant"].search(
                            [
                                ("product_id", "=", line.product_id.id),
                                ("location_id", "=", location.id),
                            ]
                        )

                        for quant in quant_ids:
                            available += quant.quantity
                        # available = line.product_id.qty_available

                        if available != 0:
                            new_lines.append(
                                [
                                    0,
                                    0,
                                    {
                                        "product_id": line.product_id.id,
                                        "old_price": line.old_price,
                                        "new_price": line.new_price,
                                        "quantity": available,
                                    },
                                ]
                            )

                    if len(new_lines) > 0:
                        self.create(
                            {
                                "name": change.name,
                                "parent_id": change.id,
                                "warehouse_id": warehouse.id,
                                "location_id": location.id,
                                "state": "done",
                                "line_ids": new_lines,
                            }
                        )
                        if warehouse.partner_id:
                            self.message_subscribe([warehouse.partner_id.id])
                        self.message_post(
                            body=_("New Price Change"),
                            type="comment",
                            subtype="mail.mt_comment",
                        )

        for change in self.filtered(lambda ch: ch.type == "product"):
            for line in change.line_ids:
                if line.product_id and not line.price_change_id.use_product_template:
                    line.product_id.with_context(ref=change.name).write({"list_price": line.new_price})
                if line.product_template_id and line.price_change_id.use_product_template:
                    line.product_template_id.with_context(ref=change.name).write({"list_price": line.new_price})
        for change in self.filtered(lambda ch: ch.type == "pricelist"):
            pricelist_lines = []
            for line in change.line_ids:
                if line.product_id and not line.price_change_id.use_product_template:
                    # delete lines with the same product variant if found
                    domain = [("pricelist_id", "=", line.pricelist_id.id), ("product_id", "=", line.product_id.id)]
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
            if self.name == "/":
                self.write({"name": self.env["ir.sequence"].next_by_code("price.change")})
        return True

    def unlink(self):
        if not self.env.context.get("force_delete", False):
            for change in self:
                if change.state not in ["draft"]:
                    raise UserError(_("Change Price document with status 'Done' cant't by deleted"))
        return super().unlink()

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            self.partner_id = self.warehouse_id.partner_id.id


class ProductPriceChangeLine(models.Model):
    _name = "product.price.change.line"
    _description = "ProductPriceChangeLine"
    _rec_name = "product_id"

    price_change_id = fields.Many2one("product.price.change", "Product Price Change", readonly=True)
    sequence = fields.Integer(
        "Sequence",
        help="Gives the sequence order when displaying a list of product with price changed.",
    )
    product_id = fields.Many2one("product.product", "Product")
    product_template_id = fields.Many2one("product.template")

    old_price = fields.Float("Old Sale Price", digits="Sale Price")
    old_amount = fields.Monetary(
        compute="_compute_old_amount",
        string="Old Amount",
        readonly=True,
        store=True,
    )

    new_price = fields.Float("New Sale Price", required=True, digits="Sale Price")
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

    quantity = fields.Float(
        "Quantity",
        digits="Product Unit of Measure",
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

    @api.depends("product_id", "product_template_id")
    def _compute_quantity(self):
        for line in self:
            if line.product_id:
                line.quantity = line.product_id.with_context(
                    warehouse=line.price_change_id.warehouse_id.id,
                    location=line.price_change_id.location_id.id,
                ).qty_available
            if line.product_template_id:
                line.quantity = line.product_template_id.with_context(
                    warehouse=line.price_change_id.warehouse_id.id,
                    location=line.price_change_id.location_id.id,
                ).qty_available

    @api.onchange("product_id", "pricelist_id", "product_template_id")
    def onchange_product_id(self):
        def get_child(location_ids, location):
            for child in location.child_ids:
                location_ids.append(child.id)
                get_child(location_ids, child)
            return location_ids

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
