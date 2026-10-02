# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## TC-001 — P1: Config download exposes station API keys across company boundaries

- **Status:** Open.
- **Location:** controllers/main.py, download_config(), /tc/config/<station_id>.
- **Trigger:** A Terrabit Connect manager restricted to company A requests the ID of a station belonging to inaccessible company B.
- **Actual behavior:** The endpoint checks manager group membership, then browses the requested station under sudo and embeds its api_key in the downloadable config. It never checks caller read access or company membership before elevating privileges.
- **Evidence:** Station company record rule inspected. Executed the actual controller method extracted through AST with a mock manager and an out-of-scope station: response contained TEST-KEY-COMPANY-B. This confirms the unchecked sudo path; no live HTTP request or real secret accessed.
- **Impact:** A company-limited manager can obtain another company's station credential. That key authenticates heartbeat, polling and result endpoints, allowing access to that station's queued payloads and submission of job results.
- **Suggested fix:** Resolve/check station read access in the caller environment before sudo-reading its restricted key, and preserve company isolation throughout the download path. Return an appropriate denial for inaccessible IDs.
- **Validation needed:** Manager with company A only downloading A/B configs, manager allowed both companies, ordinary user and nonexistent station; authenticate test keys only in isolated test fixtures.

## Review limitations

All eligible Python/XML module source manually reviewed, including authentication, queue claiming/requeue SQL locks, callback prefix restrictions, retention, manager ACLs/company rules and views. The controller reproduction uses mocked records; no database queue, HTTP integration, device request or real credential access executed.
