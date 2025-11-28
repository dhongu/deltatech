### Deltatech Project Pricelist

Project-level pricelist used when creating Sales Orders from a project or a task. Built for Odoo 19.

#### Purpose
Allow project managers to define a default pricelist on each project so that any Sales Order created from that project (or from one of its tasks) automatically uses the correct pricelist. This avoids manual selection mistakes and keeps pricing consistent.

#### Key Features
- New field on projects: `Pricelist` (`project.project.pricelist_id`).
- Project Sales Orders action injects `default_pricelist_id` so new quotations are prefilled with the project’s pricelist.
- When opening a quotation form from a project or task, `sale.order.default_get` proposes the project’s pricelist before save.
- Server-side safety: during `sale.order.create`, if a Sales Order is created from a project/task and no pricelist is provided, the project’s pricelist is applied.
- Explicit pricelist chosen by the user or provided via context is never overridden.

#### UI/Views
- Project form (simplified): displays the `Pricelist` field in the settings section.
- Project edit view inherited from `sale_project`: shows the `Pricelist` on the Settings page (visible when the project is billable and not a template).

#### Compatibility
- Odoo 19.

#### Dependencies
- `sale_project` (Project ↔ Sales integration).

#### Installation
1) Ensure your `addons_path` includes this module’s directory.
2) Install the module:
```
./odoo/odoo-bin -c odoo18.conf -d o19_playground -i deltatech_project_price_list --stop-after-init
```

#### Usage
1) Open a Project and set the `Pricelist` field.
2) Create a quotation from the project’s Sales Orders smart button, or from a task in that project.
3) The quotation’s `Pricelist` will be prefilled with the project’s pricelist and pricing will follow it.

#### Tests
Automated tests cover:
- Action context injection (`default_pricelist_id`) from the project.
- `sale.order.create` applying the project pricelist (project/task flows).
- `default_get` proposing the project pricelist when opening the SO form from project/task.
- Respect of an explicit pricelist provided by the user/context.

Run tests (on a disposable DB):
```
./odoo/odoo-bin -c odoo18.conf -d o19_test -i deltatech_project_price_list --test-tags=deltatech_project_price_list --stop-after-init
```

#### License
LGPL-3.
