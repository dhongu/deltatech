# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class CommissionCompute(models.TransientModel):
    _name = "commission.compute"
    _description = "Compute commission"

    invoice_line_ids = fields.Many2many(
        "sale.margin.report",
        "commission_compute_inv_rel",
        "compute_id",
        "invoice_line_id",
        string="Account invoice line",
    )

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)

        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("id", "in", active_ids)]
        else:
            domain = [("state", "=", "paid"), ("commission", "=", 0.0)]
        res = self.env["sale.margin.report"].search(domain)
        defaults["invoice_line_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def do_compute(self):
        res = []
        commission_days_limit_string = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("deltatech_sale_commission.days_for_commission", default=False)
        )
        commission_days_limit = 0
        if commission_days_limit_string:
            commission_days_limit = int(commission_days_limit_string)
        for line in self.invoice_line_ids:
            if commission_days_limit:
                if line.invoice_id.payment_state not in ["paid", "reversed"]:
                    if line.invoice_id.move_type == "out_refund":
                        value = {"commission": line.commission_computed}
                    else:
                        value = {"commission": 0}
                else:
                    if line.invoice_id.move_type == "out_refund":
                        value = {"commission": line.commission_computed}
                    else:
                        if not line.invoice_id.invoice_payments_widget:
                            if line.commission_computed < 0:
                                value = {"commission": line.commission_computed}
                            else:
                                value = {"commission": 0}
                        else:
                            last_payment = sorted(
                                line.invoice_id.invoice_payments_widget["content"],
                                key=lambda d: d["date"],
                                reverse=True,
                            )[0]
                            days_difference = (
                                fields.Date.to_date(last_payment["date"]) - line.invoice_id.invoice_date_due
                            ).days  # calculate the days difference between the invoice due date and the payment date
                            if days_difference <= commission_days_limit:
                                value = {"commission": line.commission_computed}
                            else:
                                value = {"commission": 0}

            else:
                value = {"commission": line.commission_computed}
            # if line.purchase_price == 0 and line.product_id:
            #     value['purchase_price'] = line.product_id.standard_price
            invoice_line = self.env["account.move.line"].browse(line.id)
            invoice_line.write(value)
            res.append(line.id)
        return {
            "domain": "[('id','in', [" + ",".join(map(str, res)) + "])]",
            "name": _("Commission"),
            "view_mode": "tree,form",
            "res_model": "sale.margin.report",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
