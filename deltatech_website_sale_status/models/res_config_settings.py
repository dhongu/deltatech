# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_detailed_stage = fields.Boolean(
        string="Detailed order stage",
        config_parameter="deltatech_website_sale_status.detailed_stage",
        help="The website quotation sent to the customer is Placed and the order stage follows the carrier "
        "status of the parcel (Pre advice, In Delivery) until the carrier delivers it. Off, the order is "
        "Delivered at the validation of the delivery. Applies to the orders whose stage is recomputed from now on.",
    )
