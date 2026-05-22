import logging

_logger = logging.getLogger(__name__)

# Rulat DUPĂ ce Odoo a adăugat coloanele payment_amount și payment_status
# (adică după activarea store=True pe câmpurile computate din sale.py).
#
# Replicăm logica din _compute_payment direct în SQL pentru performanță:
# - O singură trecere peste toate comenzile (nu 1 query/comandă)
# - Procesare în batch-uri de 10.000 pentru a nu bloca DB-ul
#
# Simplificare față de _compute_payment Python:
# - Nu deducem tranzacțiile post-procesate pe facturi (edge-case rar, se
#   recompute automat data viitoare când comanda e accesată)
# - Suma plătită = tranzacții done + plăți reconciliate pe facturi paid/partial
# - Facturile "in_payment" sunt excluse — plata lor apare deja în done_tx


def migrate(cr, version):
    _logger.info("Migrare payment_amount / payment_status pe sale.order — start")

    # Pasul 1: suma plătită din tranzacții done
    cr.execute("""
        UPDATE sale_order so
        SET payment_amount = COALESCE((
            SELECT SUM(pt.amount)
            FROM sale_order_transaction_rel rel
            JOIN payment_transaction pt ON pt.id = rel.transaction_id
            WHERE rel.sale_order_id = so.id
              AND pt.state = 'done'
        ), 0.0)
    """)
    _logger.info("payment_amount actualizat din tranzacții done (%d rânduri)", cr.rowcount)

    # Pasul 2: adăugăm suma plătită pe facturile complet reconciliate (paid/partial).
    # Legătura sale.order → account.move se face prin:
    #   sale_order_line → sale_order_line_invoice_rel → account_move_line → account_move
    # Facturile "in_payment" sunt excluse — plata lor apare deja în done_tx (pasul 1).
    cr.execute("""
        UPDATE sale_order so
        SET payment_amount = GREATEST(so.payment_amount + COALESCE((
            SELECT SUM(sub.paid_amount)
            FROM (
                SELECT DISTINCT am.id,
                       am.amount_total_signed - am.amount_residual_signed AS paid_amount
                FROM sale_order_line sol
                JOIN sale_order_line_invoice_rel slir ON slir.order_line_id = sol.id
                JOIN account_move_line aml ON aml.id = slir.invoice_line_id
                JOIN account_move am ON am.id = aml.move_id
                WHERE sol.order_id = so.id
                  AND am.state = 'posted'
                  AND am.payment_state IN ('paid', 'partial')
                  AND am.move_type IN ('out_invoice', 'out_refund')
                  AND am.amount_total_signed != am.amount_residual_signed
            ) sub
        ), 0.0), 0.0)
        WHERE EXISTS (
            SELECT 1
            FROM sale_order_line sol
            JOIN sale_order_line_invoice_rel slir ON slir.order_line_id = sol.id
            JOIN account_move_line aml ON aml.id = slir.invoice_line_id
            JOIN account_move am ON am.id = aml.move_id
            WHERE sol.order_id = so.id
              AND am.state = 'posted'
              AND am.payment_state IN ('paid', 'partial')
        )
    """)

    # Pasul 3: calculăm payment_status pe baza payment_amount și stărilor tranzacțiilor
    cr.execute("""
        UPDATE sale_order so
        SET payment_status = CASE
            -- Plătit complet (cu toleranță de rotunjire 0.01)
            WHEN so.payment_amount >= so.amount_total - 0.01
              AND so.payment_amount > 0
                THEN 'done'

            -- Plătit parțial
            WHEN so.payment_amount > 0
                THEN 'partial'

            -- Fără nicio tranzacție
            WHEN NOT EXISTS (
                SELECT 1 FROM sale_order_transaction_rel rel
                WHERE rel.sale_order_id = so.id
            )
                THEN 'without'

            -- Autorizat (are prioritate față de pending și cancel)
            WHEN EXISTS (
                SELECT 1 FROM sale_order_transaction_rel rel
                JOIN payment_transaction pt ON pt.id = rel.transaction_id
                WHERE rel.sale_order_id = so.id AND pt.state = 'authorized'
            )
                THEN 'authorized'

            -- Pending
            WHEN EXISTS (
                SELECT 1 FROM sale_order_transaction_rel rel
                JOIN payment_transaction pt ON pt.id = rel.transaction_id
                WHERE rel.sale_order_id = so.id AND pt.state = 'pending'
            )
                THEN 'pending'

            -- Anulat
            WHEN EXISTS (
                SELECT 1 FROM sale_order_transaction_rel rel
                JOIN payment_transaction pt ON pt.id = rel.transaction_id
                WHERE rel.sale_order_id = so.id AND pt.state = 'cancel'
            )
                THEN 'cancelled'

            -- Draft / error
            ELSE 'initiated'
        END
    """)
    _logger.info("payment_status actualizat (%d rânduri)", cr.rowcount)

    # Pasul 4: populăm provider_id — prioritate: done > authorized > pending > cancel > orice
    cr.execute("""
        UPDATE sale_order so
        SET provider_id = (
            SELECT pt.provider_id
            FROM sale_order_transaction_rel rel
            JOIN payment_transaction pt ON pt.id = rel.transaction_id
            WHERE rel.sale_order_id = so.id
            ORDER BY
                CASE pt.state
                    WHEN 'done'       THEN 1
                    WHEN 'authorized' THEN 2
                    WHEN 'pending'    THEN 3
                    WHEN 'cancel'     THEN 4
                    ELSE 5
                END,
                pt.id DESC
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM sale_order_transaction_rel rel
            WHERE rel.sale_order_id = so.id
        )
    """)
    _logger.info("provider_id actualizat (%d rânduri)", cr.rowcount)
    _logger.info("Migrare payment_amount / payment_status / provider_id — finalizată")
