# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models, _


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    @api.model
    def _get_operation_line(self, product, bom, qty, level, index):
        operations = super()._get_operation_line(product, bom, qty, level, index)
        operation_index = len(operations)
        company = bom.company_id or self.env.company
        currency_round = company.currency_id.round


        costs = [
            {'field': 'overhead_amount', 'name': _("Overhead Costs")},
            {'field': 'utility_consumption', 'name': _("Utility Consumption")},
            {'field': 'net_salary_rate', 'name': _("Net Salary Rate")},
            {'field': 'salary_contributions', 'name': _("Salary Contributions")},
        ]
        for cost in costs:
            if bom[cost['field']]:
                if cost['field'] == 'overhead_amount':
                    bom_cost = bom[cost['field']]
                    uom_name = _('Fixed')
                else:
                    bom_cost = bom[cost['field']] *  bom.duration
                    uom_name = _('Minutes')
                operations.append({
                    'type': 'operation',
                    'index': f"{index}{operation_index}",
                    'level': level or 0,
                    'operation': False,
                    'link_id': bom.id,
                    'link_model': 'mrp.bom',
                    'name': cost['name'],
                    'uom_name': uom_name,
                    'quantity': bom.duration * 60,
                    'bom_cost': currency_round(bom_cost),
                    'prod_cost': currency_round(bom_cost * qty),
                    'currency_id': company.currency_id.id,
                    'model': 'mrp.bom',
                })
                operation_index += 1

        return operations
