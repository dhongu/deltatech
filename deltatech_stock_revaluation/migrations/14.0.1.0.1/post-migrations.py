# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    cr.execute(
        """

            update stock_revaluation_line as sl
            SET
                serial_id = sq.lot_id
            FROM
                stock_quant as sq
            WHERE sl.quant_id = sq.id and sl.serial_id is null;

            update stock_production_lot as sl
            SET
                inventory_value = sq.cost * sq.quantity
            FROM
                stock_quant as sq
            WHERE sq.lot_id = sl.id and inventory_value is null;

    """
    )
