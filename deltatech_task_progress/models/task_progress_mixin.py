# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models

DEFAULT_PARALLEL = 3
FINISH_MODES = ("auto", "button")


class TaskProgressMixin(models.AbstractModel):
    """Runs a long task in the progress dialog, one request per item.

    On a record, the dialog calls ``record.step(item)`` for every item, ``parallel`` of them
    at the same time, each in its own request and transaction, then ``record.finish()`` and
    opens the action it returns. Without a record (``model`` given, on an empty recordset)
    the items are record ids: it calls ``model.browse(item).step()`` and, at the end,
    ``model.browse(items done).finish()``.

    A step returns the number of things it produced, added up as the counter, or a dict
    ``{"status": "success" | "warning" | "error", "message": ..., "count": ...}``: a warning
    is done and never run again (a result to check by hand), an error is run again by the
    retry button, like a step that raises. ``finish`` is called only when no item failed.

    Steps running at the same time must not write on the same rows (the record itself
    included): keep each item's result on a row of its own, or they fail with
    serialization errors. ``parallel`` above the number of HTTP workers only queues.
    """

    _name = "task.progress.mixin"
    _description = "Task Progress Mixin"

    def _task_progress_action(
        self,
        step,
        items=None,
        *,
        model=None,
        init=None,
        finish=None,
        finish_mode="auto",
        close=None,
        parallel=DEFAULT_PARALLEL,
        auto_start=True,
        show_items=False,
        title="",
        intro="",
        total=None,
        item_names=None,
        unit_label="",
        count_label="",
        detail="",
        labels=None,
    ):
        """The client action of the progress dialog.

        :param step: public method called for each item; see the class docstring
        :param items: JSON values (indexes, ids, lists of ids), one ``step`` call each;
            left empty with ``init``
        :param model: the model of the items, when the action is built on an empty
            recordset: the steps then run on the item records
        :param init: public method called on the record when the dialog opens, before the
            steps (to prepare the work); it returns ``{"items": [...]}`` and optionally
            ``item_names``, ``total`` and ``detail``
        :param finish: public method called when every item is done; the action it returns
            is opened. On a record: ``record.finish()``; without one: on the items done.
        :param finish_mode: ``auto`` calls it when the last item is done and closes the
            dialog; ``button`` shows a button (``labels["finish"]``) once the run is over,
            called on the items done even if others failed, the dialog staying open
        :param close: public method called on the record when the dialog is closed after
            a complete run; the action it returns is opened
        :param auto_start: run the items as soon as the dialog opens, otherwise on the start
            button (``labels["start"]``), after reading ``intro``
        :param show_items: list every item with its status and the step's message
        :param total: items of the whole task, when some were done before (default: items)
        :param item_names: how each item is named in the list and the errors
            (default: its value)
        :param unit_label: what an item is, in the plural ("parts", "orders")
        :param count_label: what the steps count, in the plural ("lines")
        :param detail: added to the counter ("12 pages")
        :param labels: texts of the dialog: ``running``, ``finishing``, ``preparing``,
            ``stop``, ``retry``, ``start``, ``finish``
        """
        if finish_mode not in FINISH_MODES:
            raise ValueError(f"finish_mode must be one of {FINISH_MODES}")
        if self:
            self.ensure_one()
        elif not model or init or close:
            raise ValueError("Without a record, give the model of the items, and no init or close")
        items = list(items or [])
        return {
            "type": "ir.actions.client",
            "tag": "deltatech_task_progress.run",
            "params": {
                "model": model or self._name,
                "res_id": self.id or False,
                "step": step,
                "init": init,
                "finish": finish,
                "finish_mode": finish_mode,
                "close": close,
                "items": items,
                "item_names": [str(name) for name in item_names] if item_names else [str(item) for item in items],
                "total": len(items) if total is None else total,
                "parallel": max(1, parallel or 1),
                "auto_start": auto_start,
                "show_items": show_items,
                "title": title,
                "intro": intro,
                "unit_label": unit_label,
                "count_label": count_label,
                "detail": detail,
                "labels": labels or {},
            },
        }
