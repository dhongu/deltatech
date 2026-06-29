## 19.0.1.7.0

- Process Library: support for **private HTTPS git repositories**. A token/password is sent as an HTTP Basic ``Authorization`` header on each git command (never written into the cloned repo's on-disk config), with a configurable username (default ``x-access-token`` for GitHub, ``oauth2`` for GitLab). Git now runs non-interactively, so a missing or wrong credential fails fast instead of blocking until the timeout. SSH (``git@…``) URLs and URLs that already embed credentials are used as-is.
- Library import now maps the **full process metadata** from ``process.json`` — process group, module type, implementation stage (including legacy stage keys), state — and imports the **configuration / instructing / testing / data-migration durations** that were previously dropped.
- New **"Include durations"** toggle on the library import dialog: import every selected process with or without its exported effort estimates (all-or-nothing).
