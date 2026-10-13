# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    # Feature-ul „Reserved Transfers" (buton + metoda action_view_reserved_pickings)
    # a fost eliminat la migrarea 18.0 -> 19.0. Pe bazele migrate din 18.0 view-ul
    # ramane stocat in DB si pica la revalidare ("action_view_reserved_pickings nu
    # este o actiune valida pe product.template") inainte ca Odoo sa-l curete automat.
    # Stergem view-ul orfan + ir.model.data inainte de incarcarea datelor noi.
    cr.execute(
        """
        DELETE FROM ir_ui_view
         WHERE id IN (
            SELECT res_id FROM ir_model_data
             WHERE module = 'deltatech_stock_inventory'
               AND name = 'product_template_form_reserved_pickings'
         )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = 'deltatech_stock_inventory'
           AND name = 'product_template_form_reserved_pickings'
        """
    )
