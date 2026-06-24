# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # In Odoo 19 stock valuation lives on stock.move (stock.valuation.layer was
    # removed). This flag replaces the former `active` boolean on
    # stock.valuation.layer used to "close"/exclude valuations from the storage
    # sheet. We deliberately do NOT name it `active` because Odoo treats that
    # field as magic (active_test) and would hide stock moves globally.
    l10n_ro_valuation_active = fields.Boolean(
        string="Valuation Active",
        default=True,
        help="When unset, this stock move valuation is considered closed and is "
        "excluded from the storage sheet when the 'Only active' option is used.",
    )
