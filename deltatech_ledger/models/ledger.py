from odoo import _, api, fields, models


class Ledger(models.Model):
    _name = "ledger.ledger"
    _description = "Ledger"

    name = fields.Char(string="Number of Record", default=lambda self: _("New"))
    record_date = fields.Date(string="Record Date")
    document_number = fields.Char(string="Document Number")
    place_of_origin = fields.Char(string="Place of Origin")
    record_short_description = fields.Text(string="Record Short Description")
    record_type = fields.Selection([("entry", "Entry"), ("exit", "Exit")], string="Record Type", required=True)
    contact_id = fields.Many2one("res.partner", string="Contact")
    state = fields.Selection([("active", "Active"), ("canceled", "Canceled")], string="State", default="active")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self.env["ir.sequence"].next_by_code("ledger.ledger")
            # if vals["record_type"] == "exit":
            #     vals["document_number"] = vals["name"]
            if not vals.get("record_date"):
                vals["record_date"] = fields.Date.today()
        result = super().create(vals_list)
        return result

    def button_cancel(self):
        self.write({"state": "canceled"})
