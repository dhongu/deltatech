# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class FleetReport(models.Model):
    _inherit = "fleet.vehicle.cost.report"

    # 20.0: the standard report groups the service and contract costs by service
    # type (field `service_type`), which is what this module used to add with its
    # own SQL view and the `cost_type_id` column; the standard query is kept.
    cost_type = fields.Selection(
        selection_add=[("fuel", "Fuel")],
        default="service",
        ondelete={"fuel": "set default"},
    )
