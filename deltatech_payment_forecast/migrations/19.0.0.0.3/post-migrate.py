# Copyright (c) 2024-now Terrabit Solutions All Rights Reserved

from odoo.tools import SQL


def migrate(cr, version):
    # existing rows: company from the invoice and company currency for the signed amounts
    cr.execute(
        SQL(
            """
            UPDATE payment_forecast f
               SET company_id = m.company_id,
                   currency_id = c.currency_id
              FROM account_move m
              JOIN res_company c ON c.id = m.company_id
             WHERE m.id = f.move_id
            """
        )
    )
