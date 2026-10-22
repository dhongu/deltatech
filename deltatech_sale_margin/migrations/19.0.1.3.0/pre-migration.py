# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

"""The cost price on the invoices and the margin report move from deltatech_sale_commission.

The records keep their ids: only the module of their external ids changes. Otherwise, at the end of
the update of deltatech_sale_commission, Odoo would delete them as orphans and the margin module
would create them again, losing the views that inherit them, the favourite filters and the
actions of the dashboards. This runs before the margin module loads its data, which it always
does first: deltatech_sale_commission depends on it.
"""

from odoo.tools import SQL

OLD = "deltatech_sale_commission"
NEW = "deltatech_sale_margin"

NAMES = [
    "model_sale_margin_report",
    "model_commission_update_purchase_price",
    "field_account_move_line__purchase_price",
    "view_sale_margin_report_list",
    "view_sale_margin_report_pivot",
    "view_sale_margin_report_filter",
    "action_sale_margin_report",
    "action_sale_margin_report_pivot",
    "menu_sale_margin_report_list",
    "inherit_sale_view_order_product_search",
    "invoice_form",
    "invoice_form_no_change_price",
    "view_commission_update_purchase_price_form",
    "action_commission_update_purchase_price",
    "cron_update_purchase_price",
    "cron_update_purchase_price_ir_actions_server",
    "sale_margin_report_comp_rule",
]

# the fields of the report that stay with the commissions
COMMISSION_FIELDS = [
    "commission_computed",
    "commission_manager_computed",
    "commission_director_computed",
    "commission",
    "commission_paid",
    "manager_user_id",
    "director_user_id",
]


def migrate(cr, version):
    cr.execute(SQL("SELECT 1 FROM ir_module_module WHERE name = %s AND state != 'uninstalled'", OLD))
    if cr.rowcount:
        _move_external_ids(cr)
    # A database without the commissions gets the cost price on its invoice lines. Created here, the
    # column is not computed for the whole history at the update (a search of the deliveries for
    # each invoice line): the old lines have no cost until the cost wizard is run on them.
    cr.execute(SQL("ALTER TABLE account_move_line ADD COLUMN IF NOT EXISTS purchase_price numeric"))


def _move_external_ids(cr):
    commission_fields = [f"field_sale_margin_report__{name}" for name in COMMISSION_FIELDS]
    cr.execute(
        SQL(
            """
            UPDATE ir_model_data d
               SET module = %(new)s
             WHERE d.module = %(old)s
               AND (d.name IN %(names)s
                    OR (d.name LIKE 'field\\_sale\\_margin\\_report\\_\\_%%' AND d.name NOT IN %(commission)s)
                    OR d.name LIKE 'selection\\_\\_sale\\_margin\\_report\\_\\_%%'
                    OR d.name LIKE 'field\\_commission\\_update\\_purchase\\_price\\_\\_%%')
               AND NOT EXISTS (SELECT 1 FROM ir_model_data n WHERE n.module = %(new)s AND n.name = d.name)
            """,
            new=NEW,
            old=OLD,
            names=tuple(NAMES),
            commission=tuple(commission_fields),
        )
    )
    # the many2many table of the cost wizard, so that it is not dropped with the commissions
    cr.execute(
        SQL(
            """
            UPDATE ir_model_relation
               SET module = (SELECT id FROM ir_module_module WHERE name = %(new)s)
             WHERE name = 'commission_update_purchase_price_inv_rel'
               AND module = (SELECT id FROM ir_module_module WHERE name = %(old)s)
            """,
            new=NEW,
            old=OLD,
        )
    )
