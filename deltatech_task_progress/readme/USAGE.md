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
