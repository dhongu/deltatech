Technical module: runs a long task step by step in a progress dialog, several steps at a
time, instead of a single request that times out or blocks the screen.

A model inherits `task.progress.mixin` and returns `_task_progress_action(...)` from a
button. The dialog calls the step method once per item (a page of a PDF, a batch of
records), a few in parallel, each in its own request and transaction, and shows:

- the progress bar, the items done and an estimate of the time left;
- the counter returned by the steps (lines read, records created);
- the items that failed, with their errors, and a button to run them again;
- a button to stop after the items in progress.

When every item is done, the dialog calls the finish method and opens the action it
returns (a preview, the created records). Closing is blocked while items are running.

Used by: `deltatech_ai_purchase_pdf` (vendor invoice PDF read with AI page by page).
