1. Go to **Accounting > Configuration > Settings**, in the **Vendor Bills** section check **Enable Analytic Distribution Validation** (this setting is company-specific).
2. Once enabled, every vendor bill line must have an analytic distribution that:

   - adds up to exactly 100%, and
   - has the **Location**, **Department** and **Line of Business** analytic dimensions filled in.
3. Bills that don't meet these conditions cannot be validated until the analytic distribution is corrected.
