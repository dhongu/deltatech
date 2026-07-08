## 19.0.1.9.0

- New **"Visible only to"** (``allowed_user_ids``) field on business processes: when set, the process — together with its steps, tests, step tests, issues and the process/test reports — is visible only to the listed users. Left empty (the default), nothing changes and the process stays visible to everyone. Business admins always see every process and are the only ones who can edit the field (Responsible tab).

## 19.0.1.8.2

- Import: the top-level ``developments`` and ``issues`` collections, and the per-process ``steps``, ``include_tests``, ``tests`` and ``test_steps`` keys, are now optional in the JSON file. A partial export (e.g. a single ``process.json`` from the process library) no longer fails with ``KeyError`` — missing sections are simply skipped.

## 19.0.1.8.1

- Import: the ``transaction`` key on process steps and test steps is now optional in the JSON file. Since the transaction field is no longer required, imports no longer fail with ``KeyError: 'transaction'`` when a step is exported without one — the step is simply imported without a transaction.

## 19.0.1.8.0

- **Reset to Draft** button on the business process form is now shown in every state except ``draft`` (previously hidden in ``production`` and ``draft``), so a process can be reset from any active stage.
- Passing the **implementor (internal) test** no longer advances the process state to ``ready``. Marking an internal test *Done* still records ``status_internal_test = done`` but leaves the process state unchanged; integration and user-acceptance tests continue to advance the process as before.

## 19.0.1.7.0

- Process Library: support for **private HTTPS git repositories**. A token/password is sent as an HTTP Basic ``Authorization`` header on each git command (never written into the cloned repo's on-disk config), with a configurable username (default ``x-access-token`` for GitHub, ``oauth2`` for GitLab). Git now runs non-interactively, so a missing or wrong credential fails fast instead of blocking until the timeout. SSH (``git@…``) URLs and URLs that already embed credentials are used as-is.
- Library import now maps the **full process metadata** from ``process.json`` — process group, module type, implementation stage (including legacy stage keys), state — and imports the **configuration / instructing / testing / data-migration durations** that were previously dropped.
- New **"Include durations"** toggle on the library import dialog: import every selected process with or without its exported effort estimates (all-or-nothing).
