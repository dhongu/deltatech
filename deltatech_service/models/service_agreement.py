# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceCycle(models.Model):
    _name = "service.cycle"
    _description = "Cycle"

    name = fields.Char(string="Cycle", translate=True)
    value = fields.Integer(string="Value")
    unit = fields.Selection(
        [("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year")],
        string="Unit Of Measure",
        help="Unit of Measure for Cycle.",
    )

    @api.model
    def get_cyle(self):
        self.ensure_one()
        if self.unit == "day":
            return timedelta(days=self.value)
        if self.unit == "week":
            return timedelta(weeks=self.value)
        if self.unit == "month":
            return relativedelta(months=+self.value)  # monthdelta(self.value)
        if self.unit == "year":
            return relativedelta(years=+self.value)


class ServiceAgreement(models.Model):
    _name = "service.agreement"
    _description = "Service Agreement"
    _inherit = "mail.thread"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Char(
        string="Reference", index=True, default="/", readonly=True, states={"draft": [("readonly", False)]}, copy=False
    )

    description = fields.Char(string="Description", readonly=True, states={"draft": [("readonly", False)]}, copy=False)

    date_agreement = fields.Date(
        string="Agreement Date",
        default=fields.Date.today,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )

    final_date = fields.Date(string="Final Date", readonly=True, states={"draft": [("readonly", False)]}, copy=False)

    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.user.company_id
    )

    agreement_line = fields.One2many(
        "service.agreement.line",
        "agreement_id",
        string="Agreement Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=True,
    )

    state = fields.Selection(
        [("draft", "Draft"), ("open", "In Progress"), ("closed", "Terminated")],
        string="Status",
        index=True,
        readonly=True,
        default="draft",
        copy=False,
    )

    type_id = fields.Many2one(
        "service.agreement.type", string="Type", readonly=True, states={"draft": [("readonly", False)]}
    )

    # interval de facturare

    # interval revizii

    # valoare contract ???

    display_name = fields.Char(compute="_compute_display_name")

    invoice_mode = fields.Selection(
        [("none", "Not defined"), ("service", "Group by service"), ("detail", "Detail")],
        string="Invoice Mode",
        default="none",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=_default_currency,
        domain=[("name", "in", ["RON", "EUR"])],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cycle_id = fields.Many2one(
        "service.cycle", string="Billing Cycle", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    last_invoice_id = fields.Many2one("account.move", string="Last Invoice", compute="_compute_last_invoice_id")

    invoice_day = fields.Integer(
        string="Invoice Day",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="""Day of the month, set -1 for the last day of the month.
                                 If it's positive, it gives the day of the month. Set 0 for net days .""",
    )

    next_date_invoice = fields.Date(string="Next Invoice Date", compute="_compute_last_invoice_id")

    payment_term_id = fields.Many2one("account.payment.term", string="Payment Terms")

    total_invoiced = fields.Float(string="Total invoiced", readonly=True)
    total_consumption = fields.Float(string="Total consumption", readonly=True)
    group_id = fields.Many2one(
        "service.agreement.group", string="Service Group", readonly=True, states={"draft": [("readonly", False)]}
    )

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs")

    _sql_constraints = [
        ("name_uniq", "unique(name, company_id)", "Reference must be unique per Company!"),
    ]

    def _compute_attached_docs(self):
        for task in self:
            task.doc_count = self.env["ir.attachment"].search_count(
                [("res_model", "=", "service.agreement"), ("res_id", "=", task.id)]
            )

    def attachment_tree_view(self):

        domain = ["&", ("res_model", "=", "service.agreement"), ("res_id", "in", self.ids)]

        return {
            "name": _("Attachments"),
            "domain": domain,
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "kanban,tree,form",
            "view_type": "form",
            "limit": 80,
            "context": "{{'default_res_model': '{}','default_res_id': {}}}".format(self._name, self.id),
        }

    def compute_totals(self):
        for agreement in self:
            total_consumption = 0.0
            total_invoiced = 0.0
            consumptions = self.env["service.consumption"].search([("agreement_id", "=", agreement.id)])
            invoices = self.env["account.move"]
            for consumption in consumptions:
                if consumption.state == "done":
                    total_consumption += consumption.currency_id.compute(
                        consumption.price_unit * consumption.quantity, self.env.user.company_id.currency_id
                    )
                    invoices |= consumption.invoice_id
            for invoice in invoices:
                if invoice.state in ["open", "paid"]:
                    total_invoiced += invoice.amount_untaxed
            agreement.write({"total_invoiced": total_invoiced, "total_consumption": total_consumption})

    # TODO: de legat acest contract la un cont analitic ...
    def _compute_last_invoice_id(self):
        self.last_invoice_id = self.env["account.move"].search(
            [("agreement_id", "=", self.id), ("state", "in", ["open", "paid"])], order="date desc, id desc", limit=1
        )

        if self.last_invoice_id:
            date_invoice = self.last_invoice_id.date_invoice
        else:
            date_invoice = self.date_agreement

        if date_invoice and self.cycle_id:
            next_date = fields.Date.from_string(date_invoice) + self.cycle_id.get_cyle()
            if self.invoice_day < 0:
                next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                next_date = next_first_date + relativedelta(days=self.invoice_day)
            if self.invoice_day > 0:
                next_date += relativedelta(day=self.invoice_day, months=0)

            self.next_date_invoice = fields.Date.to_string(next_date)

    @api.depends("name", "date_agreement")
    def _compute_display_name(self):
        crt_lang = self.env.user.lang
        lang = self.env["res.lang"].search([("code", "=", crt_lang)])
        lang.ensure_one()
        date_format = lang.date_format
        if self.date_agreement:
            self.display_name = self.name + " / " + self.date_agreement.strftime(date_format)
        else:
            self.display_name = self.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if ("name" not in vals) or (vals.get("name") in ("/", False)):
                sequence_agreement = self.env.ref("deltatech_service.sequence_agreement")
                if sequence_agreement:
                    vals["name"] = sequence_agreement.next_by_id()
        return super(ServiceAgreement, self).create(vals_list)

    def contract_close(self):
        return self.write({"state": "closed"})

    def contract_open(self):
        return self.write({"state": "open"})

    def contract_draft(self):
        return self.write({"state": "draft"})

    def unlink(self):
        for item in self:
            if item.state != "draft":
                raise UserError(_("You cannot delete a service agreement which is not draft."))
        return super(ServiceAgreement, self).unlink()

    # CAT, CATG CATPG


class ServiceAgreementType(models.Model):
    _name = "service.agreement.type"
    _description = "Service Agreement Type"
    name = fields.Char(string="Type", translate=True)
    journal_id = fields.Many2one("account.journal", "Journal", required=True)


class ServiceAgreementGroup(models.Model):
    _name = "service.agreement.group"
    _description = "Service Group"
    name = fields.Char(string="Service Group")


class ServiceAgreementLine(models.Model):
    _name = "service.agreement.line"
    _description = "Service Agreement Line"

    agreement_id = fields.Many2one("service.agreement", string="Contract Services", ondelete="cascade")
    product_id = fields.Many2one(
        "product.product",
        string="Service",
        ondelete="set null",
        domain=[("type", "=", "service")],
        required=False,
    )
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure")
    quantity_free = fields.Float(string="Quantity Free", digits="Product Unit of Measure")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", ondelete="set null")
    price_unit = fields.Float(string="Unit Price", required=True, digits="Service Price", default=1)
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, domain=[("name", "in", ["RON", "EUR"])]
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="agreement_id.company_id",
        store=True,
        readonly=True,
        related_sudo=False,
    )
    has_free_cycles = fields.Boolean("Has free cycles")
    cycles_free = fields.Integer(string="Free cycles", help="Free invoice cycles remaining")

    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic", ondelete="restrict")

    @api.model
    def get_value_for_consumption(self):
        # calcul pret unitar din pretul produsului daca in contract este 0
        if self.price_unit == 0.0:
            product_price_currency = self.product_id.currency_id
            product_price = self.product_id.lst_price
            price_unit = product_price_currency.with_context(date=fields.Date.context_today(self)).compute(
                product_price, self.currency_id
            )
        else:
            price_unit = self.price_unit
        quantity = self.quantity
        if self.has_free_cycles and self.cycles_free > 0:  # if there are free cycles available
            quantity = 0
        cons_value = {
            "product_id": self.product_id.id,
            "quantity": quantity,
            "price_unit": price_unit,
            "currency_id": self.currency_id.id,
        }
        return cons_value

    @api.model
    def after_create_consumption(self, consumption):
        return [consumption.id]


# e posibil ca o factura sa contina mai multe contracte
class AccountInvoice(models.Model):
    _inherit = "account.move"

    agreement_id = fields.Many2one(
        "service.agreement", string="Service Agreement", related="invoice_line_ids.agreement_line_id.agreement_id"
    )

    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        consumptions = self.env["service.consumption"].search([("invoice_id", "in", self.ids)])
        if consumptions:
            consumptions.write({"state": "draft", "invoice_id": False})
            for consumption in consumptions:
                consumption.agreement_id.compute_totals()
        return res

    def unlink(self):
        consumptions = self.env["service.consumption"].search([("invoice_id", "in", self.ids)])
        if consumptions:
            consumptions.write({"state": "draft"})
            for consumption in consumptions:
                consumption.agreement_id.compute_totals()
        return super(AccountInvoice, self).unlink()

    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        agreements = self.env["service.agreement"]
        for invoice in self:
            for line in invoice.invoice_line_ids:
                agreements |= line.agreement_line_id.agreement_id
        agreements.compute_totals()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    agreement_line_id = fields.Many2one("service.agreement.line", string="Service Agreement Line")
