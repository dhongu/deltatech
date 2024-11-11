from odoo.upgrade import util


def migrate(cr, version):
    if not version:
        return

    util.rename_field(cr, "sale.order", "stage_id", "phase_id")
    util.rename_field(cr, "stock.picking.type", "stage_id", "phase_id")
    util.rename_model(cr, "sale.order.stage", "sale.order.phase")
