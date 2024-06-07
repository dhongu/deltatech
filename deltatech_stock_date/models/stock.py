# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



from odoo import fields, models



class StockPicking(models.Model):
    _inherit = "stock.picking"

    request_effective_date = fields.Boolean(related="picking_type_id.request_effective_date")
    forced_effective_date = fields.Datetime(
        string="Forced effective date",
        help="This date will override the effective date of the stock moves",
        copy=False,
    )
    force_current_date = fields.Boolean(related="picking_type_id.force_current_date")



class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    request_effective_date = fields.Boolean(
        string="Request effective date",
        help="If checked, a required effective date field will be added to the picking form."
        "All stock moves related to the picking will be forced to this date",
    )
    force_current_date = fields.Boolean(
        string="Force current date",
        help="If checked, the effective date will be forced as the current date"
        "All stock moves related to the picking will be forced to this date",
    )
