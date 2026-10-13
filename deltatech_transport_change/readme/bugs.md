# Bug review — deltatech_transport_change

Review date: 2026-10-02. Target version: Odoo 19.

## TRANSPORT-001 — P1: All internal users can read and modify Git deployment credentials

- **Status:** Fixed in 19.0.0.1.7 — the `transport.repo` and `transport.config` ACLs are granted to `base.group_system` instead of `base.group_user`; `ssh_key`, `username` and `password` have `groups="base.group_system"`; `action_export_csv()` and the repository operations call `_check_transport_access()` (`env.is_system()`). Covered by tests in `tests/test_security.py` (internal user denied read/write/create/export, administrator keeps access).
- **Location:** security/ir.model.access.csv; models/transport_repo.py.
- **Trigger:** An ordinary internal user accesses transport.repo through ORM/RPC.
- **Actual behavior:** Both repository and configuration ACLs grant base.group_user full CRUD. Password/token and SSH key fields have no field groups, and no record rule restricts the repositories. A Settings/Technical menu and password widget do not restrict direct reads. Export uses the stored credentials to commit/push.
- **Evidence:** Complete model, ACL, view and manifest source read; only the two permissive ACLs are loaded. No authorization check occurs in public export/repository methods. No live credentials read or remote operation executed.
- **Impact:** Users without deployment-administration rights can obtain repository tokens/keys, replace credentials/branches and trigger configuration publication with administrator-configured tokens.
- **Suggested fix:** Restrict repository credentials and export operations to an explicit authorized administrator group, enforce server-side access, and protect secret fields.
- **Validation needed:** Ordinary internal/portal/administrator direct search/read/write and export calls; secret field reads must be denied for unauthorized users.

## TRANSPORT-002 — P1: Public repository writer permits arbitrary server file paths

- **Status:** Fixed in 19.0.0.1.7 — the filesystem helpers are private (`_clone_to_temp`, `_write_csv_and_update_manifest`, `_commit_and_push`) and check administrator access; `module_name` must match `^[A-Za-z0-9_]+$` (constraint and runtime check); the module and CSV paths, with symlinks resolved, must stay inside the clone root; the manifest is checked before any write. Covered by tests in `tests/test_security.py` (traversal module code, symlink escape, missing manifest without side effects, private helpers, valid write).
- **Location:** models/transport_repo.py, write_csv_and_update_manifest().
- **Trigger:** Call the public writer via ORM/RPC with a chosen repo_root or a repository module_name containing ../ or an absolute path.
- **Actual behavior:** Only filename parts are sanitized. repo_root and module_name are joined without a permitted-root/containment check, then directories and file content are written before validating the manifest. The method does not check administrative permission or that the root is a temporary clone created by the exporter.
- **Evidence:** Executed the actual AST-extracted writer under an isolated temporary parent: module_name=../outside wrote caller-supplied data to a sibling outside the clone. It remained there after the subsequent missing-manifest exception. Only disposable dummy files were written; no application files modified.
- **Impact:** An internal caller can write/overwrite files accessible to the Odoo service outside a clone. A raised database exception does not undo filesystem side effects; suitable application/data paths can be corrupted.
- **Suggested fix:** Make filesystem helpers private, require authorized export operations, validate module names and canonical paths against a server-owned clone root, and validate manifests before writing.
- **Validation needed:** Absolute/traversal module names, arbitrary repo_root, symlink escapes, missing manifests and denied users; rejected calls must have no filesystem side effects.

## TRANSPORT-003 — P2: Relational CSV values are exported as XML IDs under name-based headers

- **Status:** Open.
- **Location:** models/transport_config.py, _generate_csv_data(); models/transport_utils.py, map_xmlid().
- **Trigger:** Export a selected Many2one or Many2many field and install/update the resulting module CSV.
- **Actual behavior:** The header contains plain field names, while map_xmlid serializes related records into external IDs or model,id fallbacks. Plain relational headers instruct the Odoo importer to resolve display names, not XML IDs.
- **Evidence:** Actual utility execution serializes a country relation to base.ro; generation uses header=["id"]+field_names, yielding country_id rather than country_id:id. Compared local ir.fields.converter.db_id_for/_str_to_many2one/_str_to_many2many and ORM fix_import_export_id_paths: external-ID resolution requires an id subfield. No Odoo CSV import executed.
- **Impact:** Transported configurations with relations fail to load when no related display name equals the XML ID, or can resolve the wrong record if such a name exists. model,id fallbacks are also database-specific.
- **Suggested fix:** Build type-aware import-compatible field paths (relation/id), require or create stable external IDs for transported relations, and validate export/import round trips.
- **Validation needed:** Many2one/Many2many with XML IDs, records without IDs, duplicate names and destination database IDs differing from source.

## TRANSPORT-004 — P2: Rejected Git pushes can be reported as successful and discarded

- **Status:** Open.
- **Location:** models/transport_repo.py, commit_and_push(); models/transport_config.py, action_export_csv().
- **Trigger:** Push to an existing tracked branch is rejected, for example because the remote branch advanced or branch policy rejects the update.
- **Actual behavior:** The tracked-branch path calls origin.push and ignores its PushInfoList result. The exporter then posts Commit & push succeeded, reports a success notification, updates last_export and deletes the temporary clone. Explicitly raised clone/push exceptions are also swallowed while final status remains success.
- **Evidence:** Executed the actual AST-extracted commit method with a rejected push result: it returns normally. Inspected installed GitPython Remote.push and PushInfoList source: rejected heads are represented by ERROR flags and callers must invoke raise_if_error. No real clone/commit/push or remote request executed.
- **Impact:** Users can believe changes reached the repository when they did not. Failed exports receive a last-export timestamp, and the only local commit is removed with clone cleanup.
- **Suggested fix:** Check push results with raise_if_error and rejected/error flags, propagate failure per repository, update last_export only for confirmed successful exports and make notification/counts reflect failed groups.
- **Validation needed:** Rejected tracked push, failed clone, authentication failure, partial multi-repository success and successful/no-op exports; verify messages, timestamps and remote commit state.

## Review limitations

All eligible source was manually read. Isolated method/XML reproductions and local framework/library source inspection do not establish database or browser integration coverage. No live credentials, external repository operations, Odoo database mutations or PDF rendering executed.
