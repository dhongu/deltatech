# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceConsumption(models.Model):
    _name = "service.consumption"
    _description = "Service consumption"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Char(string="Reference", index=True, readonly=True)

    partner_id = fields.Many2one("res.partner", string="Partner", required=True, readonly=True)
    period_id = fields.Many2one("date.range", string="Period", required=True, copy=False, readonly=True)

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        ondelete="restrict",
        readonly=True,
        index=True,
        domain=[("type", "=", "service")],
    )
    quantity = fields.Float(
        string="Quantity",
        digits="Product Unit of Measure",
        readonly=True,
        states={"draft": [("readonly", False)]},
        required=True,
        default=1,
    )
    invoiced_qty = fields.Float(
        string="Invoiced Quantity", digits="Product Unit of Measure", readonly=True, default=0.0
    )
    price_unit = fields.Float(
        string="Unit Price",
        required=True,
        digits="Service Price",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=1,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=_default_currency,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="agreement_id.company_id",
        store=True,
        readonly=True,
        related_sudo=False,
    )

    state = fields.Selection(
        [("draft", "Without invoice"), ("none", "Not Applicable"), ("done", "With invoice")],
        string="Status",
        index=True,
        default="draft",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    agreement_id = fields.Many2one(
        "service.agreement", string="Agreement", readonly=True, ondelete="restrict", copy=False, index=True
    )
    agreement_line_id = fields.Many2one(
        "service.agreement.line", string="Agreement Line", readonly=True, ondelete="restrict", copy=False
    )
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic", ondelete="restrict")

    invoice_id = fields.Many2one(
        "account.move", string="Invoice Reference", ondelete="set default", readonly=True, copy=False, index=True
    )

    uom_id = fields.Many2one(
        "uom.uom", string="Unit of Measure", related="agreement_line_id.uom_id", readonly=True, copy=False
    )

    date_invoice = fields.Date(string="Invoice Date", readonly=True)
    with_free_cycle = fields.Boolean("Created with free cycle")

    _sql_constraints = [
        ("agreement_line_period_uniq", "unique(period_id,agreement_line_id)", "Agreement line in period already exist!")
    ]
    group_id = fields.Many2one(
        "service.agreement.group", string="Service Group", readonly=True, ondelete="restrict", copy=False, index=True
    )

    def unlink(self):
        for item in self:
            if item.state == "done":
                raise UserError(_("You cannot delete a service consumption which is invoiced."))
            if item.with_free_cycle:
                # incrementing the free cycle on agreement line
                cycles_free = item.agreement_line_id.cycles_free + 1
                item.agreement_line_id.write({"cycles_free": cycles_free})

        return super(ServiceConsumption, self).unlink()
