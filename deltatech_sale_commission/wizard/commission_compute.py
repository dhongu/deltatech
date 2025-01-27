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
                    full_payment_date = fields.Date.to_date("1999-01-01")  # took a date from the past
                    for payment in line.invoice_id.invoice_payments_widget[
                        "content"
                    ]:  # sometimes the payments don't reach invoice_payments_ids so we use the widget
                        if fields.Date.to_date(payment["date"]) > full_payment_date:
                            full_payment_date = fields.Date.to_date(payment["date"])  # get the latest payment date
                    days_difference = (
                        full_payment_date - line.invoice_id.invoice_date
                    ).days  # calculate the days difference between the invoice date and the payment date
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
