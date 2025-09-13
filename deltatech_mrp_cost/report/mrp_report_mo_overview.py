# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models


class ReportMoOverview(models.AbstractModel):
    _inherit = "report.mrp.report_mo_overview"

    def _get_operations_data(self, production, level=0, current_index=False):
        res = super()._get_operations_data(production, level=level, current_index=current_index)
        operations = res["details"]
        operation_index = len(operations)
        company = production.company_id or self.env.company
        currency = company.currency_id

        costs = [
            {"field": "overhead_amount", "name": _("Overhead Costs")},
            {"field": "utility_consumption", "name": _("Utility Consumption")},
            {"field": "net_salary_rate", "name": _("Net Salary Rate")},
            {"field": "salary_contributions", "name": _("Salary Contributions")},
        ]

        mo_cost = 0
        real_cost = 0
        qty = production.product_qty
        if production.qty_produced:
            qty = production.qty_produced

        for cost in costs:
            if production[cost["field"]]:
                if cost["field"] == "overhead_amount":
                    item_cost = production[cost["field"]]
                    uom_name = _("Fixed")
                else:
                    item_cost = production[cost["field"]] * production.global_duration
                    uom_name = _("Minutes")
                operation_cost = item_cost * qty
                operations.append(
                    {
                        "level": level,
                        "index": f"{current_index}W{operation_index}",
                        "name": cost["name"],
                        "quantity": production.global_duration * 60,
                        "uom_name": uom_name,
                        "uom_precision": 4,
                        "unit_cost": item_cost,
                        "mo_cost": currency.round(operation_cost),
                        "real_cost": currency.round(operation_cost),
                        "currency_id": currency.id,
                        "currency": currency,
                    }
                )
                mo_cost += operation_cost
                real_cost += operation_cost
                operation_index += 1

        res["summary"]["mo_cost"] += mo_cost
        res["summary"]["real_cost"] += real_cost
        return res
