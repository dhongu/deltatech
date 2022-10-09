# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ServiceCycle(models.Model):
    _inherit = "service.cycle"

    unit = fields.Selection(selection_add=[("counter", "From counter")], string="Unit Of Measure")

    @api.model
    def get_cycle(self):
        self.ensure_one()
        if self.unit == "counter":
            return self.value
        else:
            return super(ServiceCycle, self).get_cycle()
