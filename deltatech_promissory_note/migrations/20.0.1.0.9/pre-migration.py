# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
from odoo.tools import SQL
from odoo.tools.sql import column_exists, create_column, table_exists

FIELDS = (
    ("bank_issuer_id", "bank_issuer"),
    ("bank_beneficiary_id", "bank_beneficiary"),
)


def migrate(cr, version):
    """În 20 `res.bank` nu mai există: băncile emitentului și beneficiarului devin text.

    Numele băncii se copiază din `res_bank` înainte ca ORM-ul să renunțe la coloanele vechi,
    cât timp tabela mai există în baza migrată.
    """
    table = "promissory_note"
    for old_column, new_column in FIELDS:
        if not column_exists(cr, table, old_column):
            continue
        if not column_exists(cr, table, new_column):
            create_column(cr, table, new_column, "varchar")
        if table_exists(cr, "res_bank"):
            cr.execute(
                SQL(
                    """
                    UPDATE %(table)s note
                       SET %(new)s = bank.name
                      FROM res_bank bank
                     WHERE bank.id = note.%(old)s
                       AND note.%(new)s IS NULL
                    """,
                    table=SQL.identifier(table),
                    new=SQL.identifier(new_column),
                    old=SQL.identifier(old_column),
                )
            )
