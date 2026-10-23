In the consumer model:

```python
class MyWizard(models.TransientModel):
    _name = "my.wizard"
    _inherit = ["task.progress.mixin"]

    def action_run(self):
        return self._task_progress_action(
            "run_part",
            items=[0, 1, 2],
            finish="action_done",
            parallel=3,
            title=self.env._("Reading the document"),
            unit_label=self.env._("parts"),
            count_label=self.env._("lines"),
        )

    def run_part(self, index):
        # one item, one transaction: write the result on a row of its own
        ...
        return 12  # added to the counter

    def action_done(self):
        return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id}
```

Steps running at the same time must not write on the same row (the wizard included),
otherwise they fail with serialization errors: keep each item's result on a row of its
own and merge them in the finish method. A `parallel` higher than the number of HTTP
workers of the server only queues the requests.

Without a wizard, the steps run on the records themselves (an action of the list view):

```python
def action_send_to_carrier(self):
    return self.env["task.progress.mixin"]._task_progress_action(
        "action_send_to_carrier_one",  # called on each order: order.action_send_to_carrier_one()
        self.ids,
        model=self._name,
        item_names=self.mapped("name"),
        parallel=1,
        auto_start=False,
        show_items=True,
        intro=self.env._("Send the orders to the carrier."),
        finish="action_download_awb_labels",  # called on the orders sent
        finish_mode="button",
        labels={"start": self.env._("Send"), "finish": self.env._("Print AWBs")},
    )

def action_send_to_carrier_one(self):
    ...
    return {"status": "warning", "message": "uncertain result, check at the carrier"}
```

A step returns a number (the counter) or `{"status", "message", "count"}`: `success`,
`warning` (done, shown to check by hand, never run again) or `error` (run again by the
retry button, like a step that raises).

With `init`, the dialog first calls `record.init()`, which returns
`{"items": [...], "item_names": [...], "total": n, "detail": "..."}`: the work is prepared
on the server (a file read, a plan made) while the dialog shows *Preparing...*. With
`close`, `record.close()` is called when the dialog is closed after a complete run, and the
action it returns is opened.
