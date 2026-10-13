# ©  2025 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL, sql

_logger = logging.getLogger(__name__)

BACKFILL_SQL = SQL(
    """
    UPDATE product_image pi
       SET image_checksum = att.checksum
      FROM ir_attachment att
     WHERE att.res_model = 'product.image'
       AND att.res_field = 'image_1920'
       AND att.res_id = pi.id
       AND att.checksum IS NOT NULL
       AND pi.image_checksum IS DISTINCT FROM att.checksum
    """
)


def pre_init_hook(env):
    """Creează și populează ``image_checksum`` ÎNAINTE ca ORM-ul să vadă câmpul.

    Un câmp stocat computat adăugat pe un tabel existent face ca ORM-ul să
    marcheze **toate** rândurile pentru recompute (``models.py``: "Prepare
    computation of ..."), și o face în ``_auto_init``, adică înainte de
    ``post_init_hook``. Pe un catalog de ~70.000 imagini asta a omorât procesul
    de instalare prin depășirea limitei de memorie, fără să apuce să ruleze
    backfill-ul SQL.

    ``Field.update_db`` întoarce ``not column``, deci o coloană care există deja
    nu declanșează nicio recomputare. O creăm noi, populată, și instalarea nu
    mai are ce calcula.
    """
    if not sql.table_exists(env.cr, "product_image"):
        # website_sale nu e încă instalat; tabela se creează cu coloana la loc
        return
    env.cr.execute(SQL("ALTER TABLE product_image ADD COLUMN IF NOT EXISTS image_checksum varchar"))
    env.cr.execute(BACKFILL_SQL)
    _logger.info("deltatech_image_optimize: pre-filled %s product image checksums", env.cr.rowcount)


def post_init_hook(env):
    """Prinde imaginile apărute între pre-init și sfârșitul instalării."""
    updated = env["product.image"]._dedup_backfill_checksums()
    _logger.info("deltatech_image_optimize: backfilled %s product image checksums", updated)
