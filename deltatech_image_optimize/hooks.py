# ©  2025 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Umple ``image_checksum`` pe product.image, fără să citească imaginile.

    Compute-ul ORM ar încărca fiecare imagine din filestore; pe un catalog mare
    asta durează ore. Checksum-ul e deja calculat de Odoo în ir_attachment.
    """
    updated = env["product.image"]._dedup_backfill_checksums()
    _logger.info("deltatech_image_optimize: backfilled %s product image checksums", updated)
