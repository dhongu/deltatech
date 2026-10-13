from odoo import api, fields, models
from odoo.exceptions import ValidationError

LINKABLE_MODELS = [
    "project.project",
    "project.task",
    "helpdesk.ticket",
    "sale.order",
    "purchase.order",
    "account.move",
    "stock.picking",
]


class LedgerLink(models.Model):
    _name = "ledger.link"
    _description = "Ledger Link"
    _order = "id"

    ledger_id = fields.Many2one("ledger.ledger", string="Ledger Record", required=True, ondelete="cascade")
    link_type = fields.Selection(
        [("record", "Odoo Record"), ("url", "Web Link")], string="Type", required=True, default="record"
    )
    reference = fields.Reference(selection="_selection_reference", string="Record")
    url = fields.Char(string="URL")
    name = fields.Char(string="Label", compute="_compute_name", store=True, readonly=False)

    @api.model
    def _selection_reference(self):
        # only the models of the installed apps (e.g. helpdesk is an Enterprise app)
        return [(model, self.env[model]._description) for model in LINKABLE_MODELS if model in self.env]

    @api.depends("link_type", "reference", "url")
    def _compute_name(self):
        for link in self:
            if link.name:
                continue
            if link.link_type == "record" and link.reference:
                link.name = link.reference.display_name
            elif link.link_type == "url":
                link.name = link.url or False
            else:
                link.name = False

    @api.constrains("link_type", "reference", "url")
    def _check_target(self):
        for link in self:
            if link.link_type == "record" and not link.reference:
                raise ValidationError(self.env._("Select the record to link."))
            if link.link_type == "url" and not link.url:
                raise ValidationError(self.env._("Enter the web address to link."))
