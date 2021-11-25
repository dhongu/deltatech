# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class StockRevaluation(models.Model):
    _name = "stock.revaluation"
    _description = "Stock Revaluation"
    _inherit = "mail.thread"

    name = fields.Char(
        "Reference",
        help="Reference for the journal entry",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        default="/",
    )
    title = fields.Char(
        "Title",
        help="Title for the report",
        readonly=False,
        required=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        default="PLAN AMORTIZARE ",
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("posted", "Posted"), ("cancel", "Cancelled")],
        string="Status",
        readonly=True,
        required=True,
        default="draft",
        states={"draft": [("readonly", False)]},
    )

    # quant_ids = fields.Many2many('stock.quant', 'stock_revaluation_quant', 'valuation_id','quant_id', string='Quants')

    date = fields.Date(
        string="Date", readonly=True, required=True, states={"draft": [("readonly", False)]}, default=fields.Date.today
    )
    first_revaluation = fields.Date(string="First Revaluation")
    value_type = fields.Selection([("percent", "Percent"), ("value", "Value")], default="percent", string="Value Type")

    type = fields.Selection(
        [("reduction", "Reduction"), ("growth", "Growth")],
        default="reduction",
        string="Type",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
    )
    percent = fields.Float(string="Percent", readonly=True, required=True, states={"draft": [("readonly", False)]})

    value = fields.Float(string="Value", readonly=True, required=True, states={"draft": [("readonly", False)]})

    line_ids = fields.One2many(
        "stock.revaluation.line",
        "revaluation_id",
        string="Revaluation line",
        readonly=True,
        required=True,
        copy=True,
        states={"draft": [("readonly", False)]},
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.user.company_id,
        states={"draft": [("readonly", False)]},
    )

    currency_id = fields.Many2one("res.currency", "Currency", readonly=True, related="company_id.currency_id")

    old_amount_total = fields.Float(
        string="Old Amount Total",
        readonly=True,
    )
    new_amount_total = fields.Float(
        string="New Amount Total",
        readonly=True,
    )
    account_symbol = fields.Char(string="Cont", default="21.03")

    location_id = fields.Many2one("stock.location")

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockRevaluation, self).default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)
        active_id = self.env.context.get("active_id", False)
        model = self.env.context.get("active_model", False)

        domain = False
        if model == "stock.production.lot":
            domain = [("id", "in", active_ids)]

        if model == "stock.location":
            domain = [("location_id", "=", active_id)]
            defaults["location_id"] = active_id

        if domain:
            serials = self.env["stock.production.lot"].search(domain)
            defaults["line_ids"] = []
            for serial in serials:
                if not serial.init_value:
                    init_value = serial.inventory_value
                else:
                    init_value = serial.init_value
                defaults["line_ids"] += [
                    (
                        0,
                        0,
                        {
                            "serial_id": serial.id,
                            "product_id": serial.product_id.id,
                            "init_value": init_value,
                            "old_value": serial.value,
                            "new_value": serial.value,
                        },
                    )
                ]

        return defaults

    @api.model
    def create(self, vals):
        if ("name" not in vals) or (vals.get("name") in ("/", False)):
            sequence_revaluation = self.env.ref("deltatech_stock_revaluation.sequence_stock_revaluation")
            if sequence_revaluation:
                vals["name"] = sequence_revaluation.next_by_id()
        return super(StockRevaluation, self).create(vals)

    def do_update(self):
        self.ensure_one()
        old_amount_total = 0.0
        new_amount_total = 0.0
        for line in self.line_ids:

            if not line.serial_id.init_value:
                init_value = line.serial_id.inventory_value
            else:
                init_value = line.serial_id.init_value

            if self.value_type == "percent":
                ajust = init_value * self.percent / 100.0
            else:
                ajust = self.value

            if self.type == "reduction":
                ajust = -1 * ajust
            new_value = line.serial_id.inventory_value + ajust

            # new_cost = new_value / 1  # quant.quantity
            old_amount_total += line.serial_id.inventory_value
            new_amount_total += new_value
            values = {"init_value": init_value, "old_value": line.serial_id.inventory_value, "new_value": new_value}
            if init_value == line.serial_id.inventory_value:
                values["first_revaluation"] = self.date
            line.write(values)
        self.write({"old_amount_total": old_amount_total, "new_amount_total": new_amount_total})

        if self.env.context.get("from_serial", False):
            return {
                "domain": "[('id','=', " + str(self.id) + ")]",
                "name": _("Stock Revaluation"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "stock.revaluation",
                "view_id": False,
                "type": "ir.actions.act_window",
            }

    def do_revaluation(self):
        for line in self.line_ids:

            value = {}
            if not line.serial_id.init_value:
                init_value = line.serial_id.inventory_value
                value["init_value"] = init_value
                value["first_revaluation"] = self.date
            else:
                init_value = line.serial_id.init_value
            if self.value_type == "percent":
                ajust = init_value * self.percent / 100.0
            else:
                ajust = self.value
            if self.type == "reduction":
                ajust = -1 * ajust
            new_value = line.serial_id.inventory_value + ajust
            new_cost = new_value / 1  # line.serial_id.quantity
            value["cost"] = new_cost
            line.serial_id.write(value)
        self.write({"state": "posted"})
        if self.env.context.get("from_serials", False):
            return {
                "domain": "[('id','=', " + str(self.id) + ")]",
                "name": _("Stock Revaluation"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "stock.revaluation",
                "view_id": False,
                "type": "ir.actions.act_window",
            }


class StockRevaluationLine(models.Model):
    _name = "stock.revaluation.line"
    _description = "Inventory Revaluation Line"

    revaluation_id = fields.Many2one("stock.revaluation", "Revaluation", required=True, readonly=True)

    product_id = fields.Many2one("product.product", "Product", readonly=True, related="serial_id.product_id")

    # quant_id = fields.Many2one(
    #     "stock.quant", "Quant", required=True, ondelete="cascade", domain=[("product_id.type", "=", "product")]
    # )
    serial_id = fields.Many2one("stock.production.lot", "Serial Number", domain=[("product_id.type", "=", "product")])

    init_value = fields.Float("Value from receipt", readonly=True)

    old_value = fields.Float("Previous value", help="Shows the previous value of the equipment", readonly=True)

    new_value = fields.Float(
        "New Value",
        help="Enter the new value you wish to assign to the equipment.",
        digits="Product Price",
        copy=False,
    )

    date = fields.Date("Date", related="revaluation_id.date")
    mentor_rates = fields.Integer()
    first_revaluation = fields.Date(string="First Revaluation")

    @api.onchange("serial_id")
    def onchange_serial_id(self):

        if not self.serial_id.init_value:
            init_value = self.serial_id.inventory_value
        else:
            init_value = self.serial_id.init_value
        ajust = init_value * self.revaluation_id.percent / 100.0
        if self.revaluation_id.type == "reduction":
            ajust = -1 * ajust
        new_value = self.serial_id.inventory_value + ajust
        self.product_id = self.serial_id.product_id
        self.init_value = init_value
        self.old_value = self.serial_id.inventory_value
        self.new_value = new_value
