## Anglo-Saxon Accounting

The module adds one setting under **Accounting > Configuration > Settings**, in the
**Fiscal Localization** section (visible only to users in the `base.group_no_one`
technical group):

| Setting | Field | Effect |
|---|---|---|
| Anglo-Saxon Accounting | `company_id.anglo_saxon_accounting` | When enabled, cost of goods sold is recorded in journal entries at the time of invoicing rather than at delivery. |

This setting is company-dependent; each company in a multi-company setup can enable or
disable it independently.
