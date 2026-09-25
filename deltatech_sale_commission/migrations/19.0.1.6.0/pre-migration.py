import logging

_logger = logging.getLogger(__name__)

# Sets the company's only sales journal on the rows without journal, one row per salesperson and
# company, and only when the salesperson has no row on that journal yet: otherwise the fill itself
# would create the duplicates that the new unique constraint forbids.
FILL_JOURNAL_SQL = """
    WITH single_journal AS (
        SELECT company_id, MIN(id) AS journal_id
          FROM account_journal
         WHERE type = 'sale'
      GROUP BY company_id
        HAVING COUNT(*) = 1
    ),
    candidates AS (
        SELECT DISTINCT ON (cu.user_id, cu.company_id) cu.id, sj.journal_id
          FROM commission_users cu
          JOIN single_journal sj ON sj.company_id = cu.company_id
         WHERE cu.journal_id IS NULL
           AND NOT EXISTS (
                SELECT 1
                  FROM commission_users other
                 WHERE other.user_id = cu.user_id
                   AND other.company_id = cu.company_id
                   AND other.journal_id = sj.journal_id
           )
      ORDER BY cu.user_id, cu.company_id, cu.id
    )
"""

DELETE_EXACT_DUPLICATES_SQL = """
    DELETE FROM commission_users dup
     USING commission_users keep
     WHERE dup.journal_id IS NOT NULL
       AND keep.id < dup.id
       AND keep.user_id = dup.user_id
       AND keep.journal_id = dup.journal_id
       AND keep.company_id = dup.company_id
       AND keep.rate IS NOT DISTINCT FROM dup.rate
       AND keep.manager_rate IS NOT DISTINCT FROM dup.manager_rate
       AND keep.director_rate IS NOT DISTINCT FROM dup.director_rate
       AND keep.manager_user_id IS NOT DISTINCT FROM dup.manager_user_id
       AND keep.director_user_id IS NOT DISTINCT FROM dup.director_user_id
 RETURNING dup.id
"""

# The margin report now also matches the rate on the company, so a row filed under a company other
# than the one of its journal stops applying. The journal decides: the invoices it numbers belong
# to its company, and that is the company whose report used to pick the row up. Realigning the row
# keeps the salesperson's commission exactly as it is today, so it is done rather than reported —
# except where the right company already has a row for that salesperson and journal, which would
# be a duplicate; that one is left alone and reported.
FIX_COMPANY_SQL = """
    UPDATE commission_users cu
       SET company_id = j.company_id
      FROM account_journal j
     WHERE j.id = cu.journal_id
       AND j.company_id IS DISTINCT FROM cu.company_id
       AND j.company_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
              FROM commission_users other
             WHERE other.id <> cu.id
               AND other.user_id = cu.user_id
               AND other.journal_id = cu.journal_id
               AND other.company_id = j.company_id
       )
 RETURNING cu.id, cu.company_id
"""


def migrate(cr, version):
    """commission.users.journal_id becomes required and (user, journal, company) unique.

    A row without a journal never matched an invoice in the margin report. When the company has a
    single sales journal the row is given that journal, unless it would duplicate an existing row.
    Exact duplicates are deleted. Rows whose company is not the company of their journal are
    realigned on the journal, to keep matching the invoices they match today. The rows left without
    journal, the ones that could not be realigned, and the duplicates with different rates, are
    only reported: choosing among them is the user's decision, and the ORM keeps the constraints
    pending (with a warning) until they are cleaned up.
    """
    cr.execute(
        FILL_JOURNAL_SQL
        + """
        UPDATE commission_users cu
           SET journal_id = c.journal_id
          FROM candidates c
         WHERE cu.id = c.id
     RETURNING cu.id
        """
    )
    filled = sorted(row[0] for row in cr.fetchall())
    if filled:
        # these rows start matching invoices: the margin report is a view, so their salespersons
        # get a computed commission on the past invoices too
        _logger.warning(
            "commission.users: journal set on rows %s; their salespersons now get a computed commission, "
            "including on past invoices",
            filled,
        )
    cr.execute(FIX_COMPANY_SQL)
    realigned = sorted(row[0] for row in cr.fetchall())
    if realigned:
        _logger.warning(
            "commission.users: rows %s moved to the company of their journal; without it the report "
            "would have stopped matching them and their salespersons would have lost the commission",
            realigned,
        )
    cr.execute(
        """
        SELECT cu.id
          FROM commission_users cu JOIN account_journal j ON j.id = cu.journal_id
         WHERE j.company_id IS DISTINCT FROM cu.company_id ORDER BY cu.id
        """
    )
    wrong_company = [row[0] for row in cr.fetchall()]
    if wrong_company:
        _logger.warning(
            "commission.users: rows %s are not on the company of their journal and could not be moved "
            "(the salesperson already has a row there); the report will ignore them",
            wrong_company,
        )
    # Exact duplicates (same salesperson, journal and company, and the same rates and managers)
    # double the margin report lines; dropping them loses nothing, the oldest row is kept.
    cr.execute(DELETE_EXACT_DUPLICATES_SQL)
    deleted = sorted(row[0] for row in cr.fetchall())
    if deleted:
        _logger.warning("commission.users: exact duplicate rows %s deleted, the oldest row of each is kept", deleted)
    cr.execute("SELECT id FROM commission_users WHERE journal_id IS NULL ORDER BY id")
    missing = [row[0] for row in cr.fetchall()]
    if missing:
        _logger.warning(
            "commission.users: rows %s have no journal and match no invoice; set one or delete them", missing
        )
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
