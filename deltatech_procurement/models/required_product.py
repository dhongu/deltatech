# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class RequiredOrder(models.Model):
    _name = "required.order"
    _description = "Required Products Order"
    _inherit = "mail.thread"

    name = fields.Char(
        string="Reference",
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        default=lambda self: _("New"),
    )
    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=fields.Date.today(),
    )
    state = fields.Selection(
        [("draft", "Draft"), ("progress", "Confirmed"), ("cancel", "Canceled"), ("done", "Done")],
        string="Status",
        index=True,
        readonly=True,
        default="draft",
        copy=False,
    )

    required_line = fields.One2many(
        "required.order.line",
        "required_id",
        string="Required Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_planned = fields.Date(string="Scheduled Date", readonly=True, states={"draft": [("readonly", False)]})
    location_id = fields.Many2one(
        "stock.location",
        required=True,
        string="Procurement Location",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    group_id = fields.Many2one("procurement.group", string="Procurement Group", readonly=True)

    route_id = fields.Many2one(
        "stock.location.route", string="Route", readonly=True, states={"draft": [("readonly", False)]}
    )

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        required=True,
        string="Warehouse",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Warehouse to consider for the route selection",
    )

    comment = fields.Char(string="Comment")

    @api.model
    def default_get(self, fields_list):
        defaults = super(RequiredOrder, self).default_get(fields_list)
        central_location = self.env.ref("stock.stock_location_stock")
        defaults["location_id"] = central_location.id

        defaults["warehouse_id"] = self.env.ref("stock.warehouse0").id

        return defaults

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        self.location_id = self.warehouse_id.lot_stock_id

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("required.order") or _("New")

        result = super(RequiredOrder, self).create(vals)
        return result

    def order_done(self):
        return self.write({"state": "done"})

    def order_confirm(self):
        for order in self:
            group = self.env["procurement.group"].sudo().create({"name": order.name})
            order.write({"group_id": group.id})
            order.required_line.sudo().create_procurement()
            if not self.date_planned:
                date_planned = self.date
                for line in order.required_line:
                    if line.date_planned > date_planned:
                        date_planned = line.date_planned
                order.write({"date_planned": date_planned})

        return self.write({"state": "progress"})

    def action_cancel(self):
        self.write({"state": "cancel"})

        # for order in self:
        #
        #     # for line in order.required_line:
        #     #     line.procurement_id.cancel()
        #
        #     is_cancel = all(line.procurement_id.state == "cancel" for line in order.required_line)
        #     if is_cancel:
        #         order.write({"state": "cancel"})
        #     else:
        #         raise UserError(_("You cannot cancel a order with procurement not canceled "))

    def unlink(self):
        for order in self:
            if order.state not in ("draft", "cancel"):
                raise UserError(_("You cannot delete a order which is not draft or cancelled. "))
        return super(RequiredOrder, self).unlink()

    def check_order_done(self):
        pass
        # for order in self:
        #     is_done = True
        #     for line in order.required_line:
        #         if line.procurement_id.state != "done":
        #             is_done = False
        #     if is_done:
        #         order.order_done()


class RequiredOrderLine(models.Model):
    _name = "required.order.line"
    _description = "Required Products Order Line"

    required_id = fields.Many2one("required.order", string="Required Products Order", ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product", string="Product", ondelete="set null")
    product_qty = fields.Float(string="Quantity", digits="Product Unit of Measure")
    product_uom_id = fields.Many2one("uom.uom")
    # procurement_id = fields.Many2one("procurement.order", string="Procurement Order")
    note = fields.Char(string="Note")

    qty_available = fields.Float(related="product_id.qty_available", string="Quantity On Hand")
    virtual_available = fields.Float(related="product_id.virtual_available", string="Quantity Available")

    date_planned = fields.Datetime(
        string="Scheduled Date",
        readonly=True,
        compute="_compute_date_planned",
        store=True,
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id

    @api.depends("required_id.date", "product_id")
    def _compute_date_planned(self):
        supplierinfo = False

        for supplier in self.product_id.seller_ids:
            supplierinfo = supplier
            break

        supplier_delay = int(supplierinfo.delay) if supplierinfo else 0
        date_planned = self.required_id.date + relativedelta(days=supplier_delay)
        if self.required_id.date_planned and self.required_id.date_planned > date_planned:
            date_planned = self.required_id.date_planned

        self.date_planned = date_planned

    def create_procurement(self):
        for line in self:
            line.launch_replenishment()

    def launch_replenishment(self):
        uom_reference = self.product_id.uom_id
        quantity = self.product_uom_id._compute_quantity(self.product_qty, uom_reference)
        try:
            self.env["procurement.group"].with_context(clean_context(self.env.context)).run(
                [
                    self.env["procurement.group"].Procurement(
                        self.product_id,
                        quantity,
                        uom_reference,
                        self.required_id.location_id,  # Location
                        _("Required Order"),  # Name
                        self.required_id.name,  # Origin
                        self.required_id.warehouse_id.company_id,
                        self._prepare_run_values(),  # Values
                    )
                ]
            )
        except UserError as error:
            raise UserError(error)

    def _prepare_run_values(self):
        values = {
            "warehouse_id": self.required_id.warehouse_id,
            # 'route_ids': self.route_ids,
            "date_planned": self.date_planned,
            "group_id": self.required_id.group_id,
        }
        return values
