Call the helper once, at the end of the batch, in the method run by the cron:

```python
def _cron_do_something(self, limit=100):
    records = self.search(self._domain_to_process(), limit=limit)
    done = 0
    for record in records:
        try:
            with self.env.cr.savepoint():
                record._process()
            done += 1
        except Exception:
            _logger.exception("Processing failed for %s", record)
    remaining = self.search_count(self._domain_to_process()) if done else 0
    self.env.ref("my_module.ir_cron_do_something")._cron_report_progress(done, remaining)
```

- `done` is the number of records processed in this batch, not a running total.
- Report `remaining = 0` in dry run mode or when the rest cannot be processed.
- The cron is resolved from the running progress (scheduler or "Run manually"); the
  recordset on which the helper is called is used only for direct calls from code, so
  `self.env["ir.cron"]._cron_report_progress(...)` is enough when the same method backs
  several cron jobs.
