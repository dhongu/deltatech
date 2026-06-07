## Alternative Search Settings

Navigate to **Settings > Inventory** (the setting is injected after the *Units of Measure*
section) to configure the alternative-code search behaviour:

| Setting | System Parameter | Default | Effect |
|---|---|---|---|
| **Alternative Search** (checkbox) | `alternative.search_name` | disabled | When enabled, product name-search queries also scan alternative codes. |
| **Alternative Limit** | `alternative.limit` | 10 | Maximum number of extra results returned from the alternative-code search. |
| **Minimum Length** | `alternative.length_min` | 3 | Minimum number of characters the user must type before the alternative search is triggered. |

These three values are stored as `ir.config_parameter` system parameters and can also be
set directly via **Settings > Technical > Parameters > System Parameters** if needed.
