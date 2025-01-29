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
        for line in self.invoice_line_ids:
            commission_conditions = self.env["sale.commission.condition"].search([], order="less_than_days")
            # if we don't have commission conditions, we will use the default commission
            if not commission_conditions:
                value = {"commission": line.commission_computed}
            else:
                # if the invoice is paid, we will calculate the commission based on the payment date
                if line.invoice_id.payment_state == "paid":
                    # second condition for the case where an invoice has 0 value because of a down payment
                    if not line.invoice_id.invoice_payments_widget:
                        value = {"commission": line.commission_computed}
                    else:
                        # take the latest payment date
                        last_payment = sorted(
                            line.invoice_id.invoice_payments_widget["content"], key=lambda d: d["date"], reverse=True
                        )[0]
                        days_difference = (
                            fields.Date.to_date(last_payment["date"]) - line.invoice_id.invoice_date
                        ).days  # calculate the days difference between the invoice date and the payment date

                        if days_difference <= 0:
                            value = {"commission": line.commission_computed}
                        else:
                            checked = False
                            for condition in commission_conditions:
                                if (
                                    days_difference <= condition.less_than_days
                                ):  # they are ordered by less_than_days so we will get the first condition that is less than the days difference
                                    checked = True
                                    value = {"commission": line.commission_computed * condition.percentage / 100}
                                    break
                            if not checked:  # if we didn't find a condition that is less than the days difference, we will use the default commission
                                value = {"commission": 0}
                else:
                    value = {"commission": 0}  # if the invoice is not paid, we will not calculate the commission
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
