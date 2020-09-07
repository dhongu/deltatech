# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class ServiceBilling(models.TransientModel):
    _name = "service.billing"
    _description = "Service Billing"

    journal_id = fields.Many2one(
        "account.journal", "Journal", required=True, domain="[('type', '=',  'sale' ), ('company_id', '=', company_id)]"
    )

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)

    # facturile pot fi facute grupat dupa partner sau dupa contract
    group_invoice = fields.Selection(
        [
            ("partner", "Group by partner"),
            ("agreement", "Group by agreement"),
            ("agreement_line", "Split by agreement line"),
        ],
        string="Group invoice",
        default="agreement",
    )

    # indica daca liniile din facura sunt insumate dupa servicu

    group_service = fields.Boolean(string="Group by service", default=False)

    consumption_ids = fields.Many2many(
        "service.consumption",
        "service_billing_consumption",
        "billing_id",
        "consumption_id",
        string="Consumptions",
        domain=[("invoice_id", "=", False)],
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super(ServiceBilling, self).default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)
        if "company_id" not in defaults:
            defaults.update({"company_id": self.env.user.company_id.id})
        domain = [("state", "=", "draft"), ("company_id", "=", defaults["company_id"])]
        if active_ids:
            domain += [("id", "in", active_ids)]

        res = self.env["service.consumption"].search(domain)
        for cons in res:
            if cons.agreement_id.type_id.journal_id:
                defaults["journal_id"] = cons.agreement_id.type_id.journal_id.id
        defaults["consumption_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def add_invoice_line(self, cons, pre_invoice, price_unit, name, key):

        account_id = self.env["account.move.line"].get_invoice_line_account(
            "out_invoice", cons.product_id, "", self.env.user.company_id
        )
        invoice_line = {
            "product_id": cons.product_id.id,
            "quantity": cons.quantity - cons.agreement_line_id.quantity_free,
            "price_unit": price_unit,
            "uos_id": cons.agreement_line_id.uom_id.id,
            "name": name,
            # todo: de determinat contul
            "account_id": account_id.id,
            "invoice_line_tax_ids": [(6, 0, ([rec.id for rec in cons.product_id.taxes_id]))],
            "agreement_line_id": cons.agreement_line_id.id,
            "analytic_account_id": cons.analytic_account_id.id,
        }

        # este pt situatia in care se doreste stornarea unei pozitii
        if cons.quantity < 0:
            invoice_line["quantity"] = cons.quantity

        if pre_invoice[cons.date_invoice].get(key, False):
            is_prod = False
            if (
                self.group_service and cons.agreement_id.invoice_mode != "detail"
            ) or cons.agreement_id.invoice_mode == "service":
                for line in pre_invoice[cons.date_invoice][key]["lines"]:
                    if (
                        line["product_id"] == cons.product_id.id
                        and float_compare(line["price_unit"], invoice_line["price_unit"], precision_digits=2) == 0
                    ):
                        line["quantity"] += invoice_line["quantity"]
                        is_prod = True
                        break
            if not is_prod:
                pre_invoice[cons.date_invoice][key]["lines"].append(invoice_line)
            pre_invoice[cons.date_invoice][key]["cons"] += cons
            pre_invoice[cons.date_invoice][key]["agreement_ids"] |= cons.agreement_id
        else:
            pre_invoice[cons.date_invoice][key] = {
                "lines": [invoice_line],
                "cons": cons,
                "partner_id": cons.partner_id.id,
                # todo: dterminare cont
                # 'account_id':cons.partner_id.property_account_receivable.id,
            }

            pre_invoice[cons.date_invoice][key]["agreement_ids"] = cons.agreement_id

    def do_billing_step1(self, pre_invoice):
        for cons in self.consumption_ids:
            # convertire pret in moneda companeie

            currency = cons.currency_id.with_context(date=cons.date_invoice or fields.Date.context_today(self))
            price_unit = currency.compute(cons.price_unit, self.env.user.company_id.currency_id)
            name = cons.product_id.name

            if cons.name and (cons.agreement_id.invoice_mode == "detail" or not self.group_service):
                name += cons.name

            # if self.group_invoice == "partner":
            key = cons.partner_id.id

            if self.group_invoice == "agreement" or cons.agreement_id.invoice_mode == "detail":
                key = cons.agreement_id.id

            if self.group_invoice == "agreement_line":
                key = cons.agreement_line_id.id

            if cons.quantity > cons.agreement_line_id.quantity_free or cons.quantity < 0 or cons.with_free_cycle:
                self.add_invoice_line(cons, pre_invoice, price_unit, name, key)
                cons.write({"state": "done", "invoiced_qty": cons.quantity - cons.agreement_line_id.quantity_free})
            else:  # cons.quantity < cons.agreement_line_id.quantity_free:
                cons.write({"state": "none"})

    def do_billing(self):
        pre_invoice = {}  # lista de facuri
        agreements = self.env["service.agreement"]

        for cons in self.consumption_ids:
            pre_invoice[cons.date_invoice] = {}
            agreements |= cons.agreement_id

        self.do_billing_step1(pre_invoice)

        for cons in self.consumption_ids.filtered(lambda r: r.state == "none"):
            if self.group_invoice == "agreement" or cons.agreement_id.invoice_mode == "detail":
                key = cons.agreement_id.id
            else:
                key = cons.partner_id.id
            if pre_invoice[cons.date_invoice].get(key, False):
                # daca a fost generata o factura atunci leg si consumul de facura pentru a aparea in centralizator
                pre_invoice[cons.date_invoice][key]["cons"] += cons

        if not pre_invoice:
            raise UserError(_("No condition for create a new invoice"))

        res = []
        for date_invoice in pre_invoice:
            for key in pre_invoice[date_invoice]:
                comment = _("According to agreement ")
                payment_term_id = False
                for agreement in pre_invoice[date_invoice][key]["agreement_ids"]:
                    comment += _("%s from %s \n") % (agreement.name or "____", agreement.date_agreement or "____")
                if len(pre_invoice[date_invoice][key]["agreement_ids"]) > 1:
                    payment_term_id = False
                else:
                    for agreement in pre_invoice[date_invoice][key]["agreement_ids"]:
                        payment_term_id = agreement.payment_term_id.id
                invoice_value = {
                    # 'name': _('Invoice'),
                    "partner_id": pre_invoice[date_invoice][key]["partner_id"],
                    "journal_id": self.journal_id.id,
                    "company_id": self.company_id.id,
                    "date_invoice": date_invoice,
                    "payment_term_id": payment_term_id,
                    # todo: de determinat contul
                    # 'account_id': pre_invoice[date_invoice][key]['account_id'],
                    "type": "out_invoice",
                    "state": "draft",
                    "invoice_line_ids": [(0, 0, x) for x in pre_invoice[date_invoice][key]["lines"]],
                    "comment": comment,
                    # 'agreement_id':pre_invoice[key]['agreement_id'],
                }
                invoice_id = self.env["account.move"].create(invoice_value)
                # todo: de determinat care e butonul de calcul tva
                # invoice_id.button_compute(True)
                pre_invoice[date_invoice][key]["cons"].write({"invoice_id": invoice_id.id})
                res.append(invoice_id.id)

        agreements.compute_totals()

        action = self.env.ref("deltatech_service.action_service_invoice").read()[0]
        action["domain"] = "[('id','in', [" + ",".join(map(str, res)) + "])]"
        return action
