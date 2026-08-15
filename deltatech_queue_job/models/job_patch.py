# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
"""Completarea datei de anulare pentru joburile anulate în lanț.

``Job.cancel_dependent_jobs()`` anulează dependenții printr-un UPDATE SQL brut
care scrie doar coloana ``state``, nu și ``date_cancelled``. Cronul
``queue.job.autovacuum()`` selectează însă joburile de șters exact după
``date_done`` sau ``date_cancelled``, așa că un job anulat pe această cale nu
este eliminat niciodată, oricât ar trece.

Pe o instanță de producție se adunaseră astfel 189.644 de joburi anulate fără
dată — 53% din tabel — toate ``marketplace_write`` anulate în lanț la
sincronizarea cu marketplace-urile.

``cancel_dependent_jobs`` aparține clasei ``Job``, care nu e un model ORM și nu
poate fi extinsă prin ``_inherit``; de aceea o completăm aici prin înlocuirea
metodei. Interogarea nu poate fi corectată la sursă pentru că e generată de
``_get_common_dependent_jobs_query()``, folosită și de ``enqueue_waiting()``,
unde o dată de anulare ar fi greșită.
"""

import logging

from odoo.tools import SQL

from odoo.addons.queue_job.job import CANCELLED, Job

_logger = logging.getLogger(__name__)

_cancel_dependent_jobs_original = Job.cancel_dependent_jobs


def cancel_dependent_jobs(self):
    """Anulează dependenții, apoi le pune data de anulare lipsă."""
    _cancel_dependent_jobs_original(self)
    if not self.graph_uuid:
        return
    self.env.cr.execute(
        SQL(
            "UPDATE queue_job SET date_cancelled = now() "
            "WHERE graph_uuid = %s AND state = %s AND date_cancelled IS NULL",
            self.graph_uuid,
            CANCELLED,
        )
    )
    if self.env.cr.rowcount:
        _logger.debug(
            "Stamped date_cancelled on %d dependent job(s) of graph %s",
            self.env.cr.rowcount,
            self.graph_uuid,
        )
        self.env["queue.job"].invalidate_model(["date_cancelled"])


Job.cancel_dependent_jobs = cancel_dependent_jobs
