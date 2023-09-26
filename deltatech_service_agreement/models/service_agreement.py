# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceAgreement(models.Model):
    _name = "service.agreement"
    _description = "Service Agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]

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

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)
    company_currency_id = fields.Many2one("res.currency", string="Company Currency", related="company_id.currency_id")

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
        default=lambda self: self.env.company.currency_id,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cycle_id = fields.Many2one(
        "service.cycle", string="Billing Cycle", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )

    invoice_day = fields.Integer(
        string="Invoice Day",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="""Day of the month, set -1 for the last day of the month.
                                 If it's positive, it gives the day of the month. Set 0 for net days .""",
    )

    prepare_invoice_day = fields.Integer(
        string="Prepare Invoice Day",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=-1,
        help="""Day of the month, set -1 for the last day of the month.
                                 If it's positive, it gives the day of the month. Set 0 for net days .""",
    )

    # se va seta automat la postarea facturii. Am scos  # compute="_compute_last_invoice_id")
    last_invoice_id = fields.Many2one("account.move", string="Last Invoice")
    last_date_invoice = fields.Date(string="Last Invoice Date", compute="_compute_next_date_invoice", store=True)
    next_date_invoice = fields.Date(string="Next Invoice Date", compute="_compute_next_date_invoice", store=True)

    payment_term_id = fields.Many2one("account.payment.term", string="Payment Terms")

    total_invoiced = fields.Float(string="Total invoiced", readonly=True)
    total_consumption = fields.Float(string="Total consumption", readonly=True)

    invoicing_status = fields.Selection(
        [("", "N/A"), ("unmade", "Unmade"), ("progress", "In progress"), ("done", "Done")],
        string="Invoicing Status",
        # compute="_compute_invoicing_status",
        store=True,
    )

    billing_automation = fields.Selection(
        [("auto", "Auto"), ("manual", "Manual")], string="Billing automation", default="manual"
    )

    notes = fields.Text(string="Notes")

    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.user,
    )

    group_id = fields.Many2one(
        "service.agreement.group", string="Service Group", readonly=True, states={"draft": [("readonly", False)]}
    )

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs")

    _sql_constraints = [
        ("name_uniq", "unique(name, partner_id, company_id)", "Reference must be unique!"),
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

    def show_invoices(self):
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_service_agreement.action_service_invoice")
        domain = [
            ("invoice_line_ids.agreement_id", "=", self.id),
            ("state", "=", "posted"),
            ("move_type", "=", "out_invoice"),
        ]
        invoices = self.env["account.move"].search(domain)
        action["domain"] = [("id", "=", invoices.ids)]
        return action

    def compute_totals(self):
        for agreement in self:
            total_consumption = 0.0
            total_invoiced = 0.0
            consumptions = self.env["service.consumption"].search([("agreement_id", "=", agreement.id)])
            invoices = self.env["account.move"]
            for consumption in consumptions:
                if consumption.state == "done":
                    total_consumption += consumption.revenues
                    invoices |= consumption.invoice_id
            for invoice in invoices:
                if invoice.state == "posted":
                    for line in invoice.invoice_line_ids:
                        if line.agreement_line_id in agreement.with_context(test_active=False).agreement_line:
                            total_invoiced += line.price_subtotal
            agreement.write({"total_invoiced": total_invoiced, "total_consumption": total_consumption})

    # TODO: de legat acest contract la un cont analitic ...
    @api.depends("last_invoice_id")
    def _compute_next_date_invoice(self):
        # query = """
        #     select distinct *
        #         from  (
        #             select am.id, aml.agreement_id,
        #                    rank() over (partition by aml.agreement_id  order by am.date desc) as rnk
        #             from account_move as am
        #             join account_move_line as aml on am.id = aml.move_id
        #             where am.state = 'posted' and move_type = 'out_invoice' and  agreement_line_id is not null
        #         ) as ts
        #
        #         where rnk = 1 ;
        # """

        for agreement in self:
            if not agreement.last_invoice_id:
                domain = [
                    ("invoice_line_ids.agreement_id", "=", agreement.id),
                    ("state", "=", "posted"),
                    ("move_type", "=", "out_invoice"),
                ]
                agreement.last_invoice_id = self.env["account.move"].search(domain, order="date desc, id desc", limit=1)

            if agreement.last_invoice_id:
                invoice_date = agreement.last_invoice_id.invoice_date
                agreement.last_date_invoice = invoice_date
            else:
                invoice_date = agreement.date_agreement
                agreement.last_date_invoice = False

            if invoice_date and agreement.cycle_id:
                next_date = invoice_date + agreement.cycle_id.get_cycle()
                if agreement.invoice_day < 0:
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=agreement.invoice_day)
                if agreement.invoice_day > 0:
                    next_date += relativedelta(day=agreement.invoice_day, months=0)

                agreement.next_date_invoice = next_date  # fields.Date.to_string(next_date)

    @api.depends("name", "date_agreement")
    def _compute_display_name(self):
        crt_lang = self.env.user.lang
        lang = self.env["res.lang"].search([("code", "=", crt_lang)])
        lang.ensure_one()
        date_format = lang.date_format
        for agreement in self:
            if agreement.date_agreement:
                agreement.display_name = agreement.name + " / " + agreement.date_agreement.strftime(date_format)
            else:
                agreement.display_name = agreement.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if ("name" not in vals) or (vals.get("name") in ("/", False)):
                sequence_agreement = self.env.ref("deltatech_service_agreement.sequence_agreement")
                if sequence_agreement:
                    vals["name"] = sequence_agreement.next_by_id()
        return super().create(vals_list)

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
        return super().unlink()

    def get_agreements_auto_billing(self):
        agreements = self.search([("billing_automation", "=", "auto"), ("state", "=", "open")])
        for agreement in agreements:
            # check billing prepare date
            if agreement.next_date_invoice != fields.Date.context_today(self):
                agreements = agreements - agreement
        return agreements

    @api.model
    def make_billing_automation(self):
        agreements = self.get_agreements_auto_billing()
        from_date = fields.Date.context_today(self) + relativedelta(day=1, months=0, days=0)
        to_date = fields.Date.context_today(self) + relativedelta(day=1, months=1, days=-1)
        domain = [("date_start", "=", from_date), ("date_end", "=", to_date)]
        service_period = self.env["service.date.range"].search(domain)
        domain = [("service_period_id", "in", service_period.ids), ("agreement_id", "in", agreements.ids)]
        consumptions = self.env["service.consumption"].search(domain)
        for consumption in consumptions:  # check if has consumptions in current period
            agreements = agreements - consumption.agreement_id
        if agreements:
            wizard_preparation = self.env["service.billing.preparation"]
            wizard_preparation = wizard_preparation.with_context(active_ids=agreements.ids).create({})
            res = wizard_preparation.do_billing_preparation()
            if res:
                self = self.with_context(auto=True)
                wizard_billing = self.env["service.billing"].with_context(active_ids=res["consumption_ids"]).create({})
                wizard_billing.do_billing()


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
    _order = "sequence,id desc,agreement_id"

    sequence = fields.Integer(
        string="Sequence", default=1, help="Gives the sequence of this line when displaying the agreement."
    )
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

    active = fields.Boolean(default=True)  # pentru a ascunde liniile din contract care nu
    invoice_description = fields.Char(string="Invoice Description")

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
            date = fields.Date.context_today(self)
            price_unit = product_price_currency._convert(product_price, self.currency_id, self.env.company, date)
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
        pass

    def do_billing_preparation(self, service_period_id):
        consumptions = self.env["service.consumption"]
        for line in self:
            agreement = line.agreement_id
            cons_value = line.get_value_for_consumption()
            if cons_value:
                from_uninstall = False
                if self.env.context.get("from_uninstall"):
                    from_uninstall = True
                cons_value.update(
                    {
                        "partner_id": agreement.partner_id.id,
                        "service_period_id": service_period_id.id,
                        "agreement_id": agreement.id,
                        "agreement_line_id": line.id,
                        "date_invoice": agreement.next_date_invoice,
                        "group_id": agreement.group_id.id,
                        "analytic_account_id": line.analytic_account_id.id,
                        "state": "draft",
                        "from_uninstall": from_uninstall,
                    }
                )
                consumption = self.env["service.consumption"].create(cons_value)
                if consumption:
                    if line.has_free_cycles and line.cycles_free > 0:
                        new_cycles = line.cycles_free - 1
                        line.write({"cycles_free": new_cycles})  # decrementing free cycle
                        consumption.update(
                            {"with_free_cycle": True}
                        )  # noting that was created with free cycle - used to increment it back on delete
                line.after_create_consumption(consumption)
                consumptions |= consumption

        return consumptions
