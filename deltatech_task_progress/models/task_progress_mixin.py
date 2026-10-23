# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models

DEFAULT_PARALLEL = 3


class TaskProgressMixin(models.AbstractModel):
    """Runs a long task in the progress dialog, one request per item.

    The dialog calls ``step(item)`` on the record for every item, ``parallel`` of them at
    the same time, each in its own request and transaction, then calls ``finish()`` and
    opens the action it returns. A failed item can be run again; ``finish`` is called only
    when every item succeeded.

    Steps running at the same time must not write on the same rows (the record itself
    included): keep each item's result on a row of its own, or they fail with
    serialization errors. ``parallel`` above the number of HTTP workers only queues.
    """

    _name = "task.progress.mixin"
    _description = "Task Progress Mixin"

    def _task_progress_action(
        self,
        step,
        items,
        *,
        finish=None,
        parallel=DEFAULT_PARALLEL,
        title="",
        total=None,
        item_names=None,
        unit_label="",
        count_label="",
        detail="",
        labels=None,
    ):
        """The client action of the progress dialog.

        :param step: public method called as ``record.step(item)``; it returns the number
            of things it produced (lines, records), added up as the counter, or nothing
        :param items: JSON values (indexes, ids, lists of ids), one ``step`` call each
        :param finish: public method called on the record when every item is done; the
            action it returns is opened, nothing closes the dialog
        :param total: items of the whole task, when some were done before (default: items)
        :param item_names: how each item is named in the errors (default: its value)
        :param unit_label: what an item is, in the plural ("parts", "batches")
        :param count_label: what the steps count, in the plural ("lines")
        :param detail: added to the counter ("12 pages")
        :param labels: texts of the dialog: ``running``, ``finishing``, ``stop``, ``retry``
        """
        self.ensure_one()
        items = list(items)
        return {
            "type": "ir.actions.client",
            "tag": "deltatech_task_progress.run",
            "params": {
                "model": self._name,
                "res_id": self.id,
                "step": step,
                "finish": finish,
                "items": items,
                "item_names": [str(name) for name in item_names] if item_names else [str(item) for item in items],
                "total": len(items) if total is None else total,
                "parallel": max(1, parallel or 1),
                "title": title,
                "unit_label": unit_label,
                "count_label": count_label,
                "detail": detail,
                "labels": labels or {},
            },
        }
