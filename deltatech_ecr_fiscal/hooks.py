# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
"""Preia câmpurile de audit fiscal de la modulele care le declarau înainte.

`fiscal_receipt_number`, `fiscal_doc_number`, `fiscal_z`, `fiscal_state` și
`fiscal_error` erau definite de două ori: pe `pos.order` în `deltatech_pos` și,
identic, pe `account.move` în `deltatech_sale_store`. Acum sunt declarate o singură
dată aici, iar cele două module doar moștenesc mixinul.

Rândurile din `ir_model_data` trebuie să schimbe proprietarul **înainte** ca modulele
donoare să fie actualizate. Altfel Odoo curăță înregistrările care nu mai sunt
declarate de ele și șterge coloanele din baza de date, împreună cu numerele de bon
fiscal deja înregistrate — o pierdere de pistă de audit fiscal, ireversibilă.

Rulează ca `pre_init_hook`, nu ca migrare pe modulele donoare: acest modul le e
dependență, deci se instalează primul, iar hook-ul se execută înainte ca propriile
lui `ir_model_data` să fie create. O migrare pe `deltatech_pos` ar rula prea târziu.
"""

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

NEW_MODULE = "deltatech_ecr_fiscal"

FIELD_NAMES = (
    "fiscal_receipt_number",
    "fiscal_doc_number",
    "fiscal_z",
    "fiscal_state",
    "fiscal_error",
)

# {modul_donor: (modele,)} — modelul dă forma xml id-ului
# (`field_<model_cu_underscore>__<câmp>`).
#
# `account.bank.statement.line` apare fiindcă delegă către `account.move`
# (`_inherits`): orice câmp adăugat pe factură produce și un `ir.model.fields`
# delegat pe linia de extras, deținut de același modul. Fără el în listă, cinci
# rânduri ar rămâne pe modulul donor și ar fi curățate la actualizarea lui.
DONORS = {
    "deltatech_pos": ("pos.order",),
    "deltatech_sale_store": ("account.move", "account.bank.statement.line"),
}


def _moved_xml_ids(model):
    prefix = f"field_{model.replace('.', '_')}__"
    return tuple(f"{prefix}{name}" for name in FIELD_NAMES)


def pre_init_hook(env):
    for donor, models in DONORS.items():
        for model in models:
            _take_over(env, donor, model)


def _take_over(env, donor, model):
    xml_ids = _moved_xml_ids(model)
    env.cr.execute(
        SQL(
            """
            UPDATE ir_model_data d
               SET module = %s
             WHERE d.module = %s
               AND d.model = 'ir.model.fields'
               AND d.name IN %s
               AND NOT EXISTS (
                     SELECT 1
                       FROM ir_model_data other
                      WHERE other.module = %s
                        AND other.name = d.name
                   )
            """,
            NEW_MODULE,
            donor,
            xml_ids,
            NEW_MODULE,
        )
    )
    if env.cr.rowcount:
        _logger.info(
            "ECR fiscal fields: took over %s field records from %s (%s)",
            env.cr.rowcount,
            donor,
            model,
        )
