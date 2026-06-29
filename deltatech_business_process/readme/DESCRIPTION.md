Business Process Management for Odoo

This module helps you structure and execute business implementation projects in Odoo. It introduces Projects, Business Processes and their Steps, along with Testing and Issue tracking flows so teams can design, validate and deliver processes in a controlled way.

Key features
- Project workspace: manage implementation projects, phases and overall progress.
- Business Processes: define processes per project, grouped by business area and optionally by process group.
- Steps: break down each process into ordered steps with responsible parties and related transactions.
- Testing: create Internal, Integration and User Acceptance Tests that mirror the process steps and track execution status and results per step.
- Issues: log issues against a process or a specific test step, follow up through states, and close with validations.
- Developments: link development items to processes and/or projects to track required customizations.
- Attachments: quick access to all related documents across project, processes, steps, tests and issues.
- Reports: print Business Process and Process Test reports; export/import processes as JSON for reuse.

Data model at a glance
- business.project: the project container; aggregates processes, issues, developments and attachments; can generate an Excel summary report.
- business.process: the core entity describing a process within a project; has steps, tests, developments and computed counters.
- business.process.step: an ordered activity in a process; can reference a business transaction and a responsible partner.
- business.process.test: a test instance for a process (scope: internal/integration/user_acceptance); auto-generates step tests; tracks progress and completion.
- business.process.step.test: mirrors a process step for a specific test; records dates, result (draft/passed/failed) and observations; counts linked issues.
- business.issue: issues discovered during testing or execution; life‑cycle from draft → open/allocated → solved/in_test → closed/reopened; integrates with followers and email.
- business.development (+ type): reference developments linked to processes/projects; can contribute to project duration.
- business.area and business.process.group: classify processes by area and group.

Typical workflows
1) Design
- Create a Project, define Business Areas and (optionally) Process Groups.
- Add Business Processes and their Steps; set responsibles and expected durations.

2) Testing
- Start tests from a process (internal/integration/UAT). The module creates corresponding test records and step tests.
- Run tests, record results per step, and raise issues directly on the affected step test.
- Closing issues can automatically mark a step test as passed when no other issues remain open for that step test.

3) Go‑live
- When all required tests are done, move the process to Ready and then to Production.

Export/Import
- From the Business Processes list view, export processes as JSON. You can choose to include tests, responsible, customer and support info.
- On the Project form, import a previously exported JSON to bootstrap a project.
- Important: for smooth import across databases, ensure the names for Responsible/Customer Responsible/Support are consistent; otherwise new contacts may be created during import if they do not exist.

Attachments and counts
- Project and Process records compute document counts and provide an Attachment smart button that opens a consolidated view of attachments related to the record and its tests.

Excel report
- From a Project, generate an Excel summary that groups processes by Area and aggregates configuration/instruction/testing/data‑migration durations, highlighting processes with zero total duration.

Security and chatter
- Most records inherit mail.thread/activity to enable followers, logging and notifications. Key participants (responsibles, testers, step responsibles, customer contacts) are subscribed automatically during actions where relevant.

Installation
- Dependencies: base, mail.
- Install the module like any standard Odoo addon and ensure sequences and email templates from data files are loaded.

Process Library
- A reusable library of processes can be sourced from installed modules that ship a `processes/` folder and/or from external git repositories (Settings → Process Library).
- Configure the git repositories as a comma-separated list of URLs and press "Sync now" to clone/pull them locally; processes are then imported selectively into a project via the "Process Library" action.
- The library import maps the full process metadata exported in `process.json` — area, process group, module type, implementation stage, state — and brings in the configuration / instructing / testing / data-migration durations. An "Include durations" toggle on the import dialog lets you import every selected process with or without its effort estimates (all-or-nothing).
- Private HTTPS repositories: set a Git username (default `x-access-token` for GitHub, `oauth2` for GitLab) and a token/password. The token is sent as an HTTP Basic Authorization header on each git command and is never written into the cloned repo's on-disk config. SSH (`git@…`) URLs use their own keys; URLs that already embed credentials are used as-is.

Configuration tips
- Define Business Areas and Process Groups first to better organize processes.
- For local projects, you can use the Install Modules button on a process to (optionally) install selected modules; remote projects are blocked by design.

Compatibility
- Designed for Odoo 19.0.

Maintainers
- Terrabit, Dorin Hongu

License
- OPL-1. See README.rst at the addons root for license details.
