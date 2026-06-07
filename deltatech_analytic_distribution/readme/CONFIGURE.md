To enable analytic distribution enforcement for a company:

1. Go to **Accounting** > **Configuration** > **Settings**.
2. Scroll to the **Vendor Bills** section.
3. Enable the checkbox **Enable Analytic Distribution Validation**.
4. Click **Save**.

Once enabled, every vendor bill line must have an analytic distribution that:

- is present (cannot be empty),
- sums to exactly 100%,
- contains exactly three analytic dimensions: Location, Department, and Line of Business.

This setting is **company-specific** — each company in a multi-company setup can have it
enabled or disabled independently.
