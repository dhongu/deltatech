## 19.0.0.1.8 (2026-10-17)

- Many2one and Many2many fields were exported with a plain `field` header while the
  values were external IDs, so the target database looked them up by name and failed
  or picked the wrong record. Relational columns now use the `field/id` header, and
  related records without an external ID get a stable `__export__` one instead of a
  database-specific `model,id` value.
- A push rejected by the remote (for example because the branch had advanced) was
  reported as a success and the export date was updated. The push result is now
  checked: the chatter shows the failure, the notification warns about the failed
  repositories, and the export date is set only for the configurations that reached
  the repository.

## 19.0.0.1.7 (2026-10-02)

- Security: every internal user could read and change the Git repositories, including
  the token/password and SSH key, and run exports with them. The repository and export
  configuration models, and the credential fields, are now reserved to Settings
  administrators (`base.group_system`); the export checks it on the server too.
  **Behavior change:** non-administrator users lose access to the Transport menus.
- Security: the public `write_csv_and_update_manifest()` accepted any `repo_root` and a
  module code such as `../outside`, so it could write files anywhere on the server.
  The repository helpers are now private (`_clone_to_temp`, `_write_csv_and_update_manifest`,
  `_commit_and_push`), the module code may contain only letters, digits and underscores,
  the target path (symlinks resolved) must stay inside the clone, and the module manifest
  is checked before anything is written.

## 19.0.0.1.6 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.0.1.5 (2026-09-23)

- `except: pass` blocks replaced with `contextlib.suppress` for the same exceptions;
  behavior is unchanged. The test tear-downs use the same pattern.
