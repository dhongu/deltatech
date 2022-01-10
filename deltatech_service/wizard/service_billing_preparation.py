# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class ServiceBillingPreparation(models.TransientModel):
    _name = "service.billing.preparation"
    _description = "Service Billing Preparation"

    period_id = fields.Many2one(
        "date.range",
        string="Period",
        required=True,
    )
    agreement_ids = fields.Many2many(
        "service.agreement",
        "service_billing_agreement",
        "billing_id",
        "agreement_id",
        string="Agreements",
        domain=[("state", "=", "open")],
    )

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)

    @api.model
    def default_get(self, fields_list):
        defaults = super(ServiceBillingPreparation, self).default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)
        if "company_id" not in defaults:
            defaults.update({"company_id": self.env.user.company_id.id})
        domain = [("state", "=", "open"), ("company_id", "=", defaults["company_id"])]
        if active_ids:
            domain += [("id", "in", active_ids)]

        res = self.env["service.agreement"].search(domain)
        defaults["agreement_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def do_billing_preparation(self):
        # res = []
        consumptions = self.env["service.consumption"]
        for agreement in self.agreement_ids:
            consumptions = agreement.agreement_line.do_billing_preparation(self.period_id)
        self.agreement_ids.compute_totals()
        return {
            # "domain": "[('id','in', [" + ",".join(map(str, res)) + "])]",
            "domain": [("id", "in", consumptions.ids)],
            "name": _("Service Consumption"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.consumption",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
