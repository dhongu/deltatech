from odoo import api, fields, models


class SaleStore(models.TransientModel):
    _inherit = "sale.store"

    deltatech_operation_unit = fields.Many2many("deltatech.operating.unit", compute="_compute_operation_unit_domain")

    @api.depends("payment_journal_id")  # daca n-ai depends nu se apeleaza la deschidere wizard
    def _compute_operation_unit_domain(self):
        for record in self:
            user_groups = self.env.user.groups_id.ids
            operating_units = self.env["deltatech.operating.unit"].search(
                [("groups_ids", "in", user_groups)]
            )  # ar trebui sa vedem doar unitatile din care userul face parte
            record.deltatech_operation_unit = operating_units
