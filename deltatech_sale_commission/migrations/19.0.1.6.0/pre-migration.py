import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """commission.users.journal_id becomes required and (user, journal, company) unique.

    A row without a journal never matched an invoice in the margin report. When its company has
    a single sales journal there is no doubt which one was meant, so it is filled in; the other
    rows, and the duplicates, are only reported: choosing among them is the user's decision, and
    the ORM keeps the constraint pending (with a warning) until they are cleaned up.
    """
    cr.execute(
        """
        UPDATE commission_users cu
           SET journal_id = j.id
          FROM (SELECT company_id, MIN(id) AS id
                  FROM account_journal
                 WHERE type = 'sale'
              GROUP BY company_id
                HAVING COUNT(*) = 1) j
         WHERE cu.journal_id IS NULL
           AND j.company_id = cu.company_id
        """
    )
    if cr.rowcount:
        _logger.info("commission.users: journal set on %s rows without journal", cr.rowcount)
    cr.execute("SELECT id FROM commission_users WHERE journal_id IS NULL")
    missing = [row[0] for row in cr.fetchall()]
    if missing:
        _logger.warning("commission.users: rows %s have no journal and match no invoice; set one", missing)
    cr.execute(
        """
        SELECT user_id, journal_id, company_id, ARRAY_AGG(id ORDER BY id)
          FROM commission_users
         WHERE journal_id IS NOT NULL
      GROUP BY user_id, journal_id, company_id
        HAVING COUNT(*) > 1
        """
    )
    for user_id, journal_id, company_id, ids in cr.fetchall():
        _logger.warning(
            "commission.users: rows %s duplicate user %s on journal %s (company %s); keep only one",
            ids,
            user_id,
            journal_id,
            company_id,
        )
