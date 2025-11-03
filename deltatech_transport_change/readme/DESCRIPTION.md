DeltaTech Transport Change

DeltaTech Transport Change is an Odoo technical module designed to manage the export of configuration changes and transport them between environments (Development → Staging → Production) in a structured and version-controlled manner. The module provides a functionality similar to SAP transport requests, allowing system administrators and consultants to track, export, and migrate configuration data safely.

Key Features

Export Configuration to CSV/XML: Easily export selected models, fields, and records with optional domain filters, triggered from a form button or list server action. The first column in the generated CSV is always the External ID (`id`) of each record, ensuring reliable re-import and cross-environment consistency.

Mapping of Relationships: Automatically converts many2one and many2many relational fields to XMLID references for reliable transport.

Repo Integration: Stores information about client modules, Git repository URLs, branches, and credentials to facilitate version-controlled deployment.

Git Automation: Supports automatic commit and optional push of exported configuration files to the repository.

Environment Transport: Enables safe migration of configuration changes from Development to Staging and Production environments.

Extensible & Configurable: Add new models, fields, and export configurations without modifying the module core.

Use Case

Ideal for clients with multiple Odoo instances where configuration changes need to be applied consistently and traceably across environments. Helps maintain reproducibility, auditability, and version control for technical configuration data.
