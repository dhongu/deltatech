from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    deltatech_operating_unit_id = fields.Many2one("deltatech.operating.unit", string="Operational Unit")

    # user_groups = self.env.user.groups_id.ids
    # record.payment_journal_domain = "[('sale_store_status', 'in', ['bf_only', 'all']), ('deltatech_operating_unit_id.groups_ids', 'in', %s)]" % user_groups
