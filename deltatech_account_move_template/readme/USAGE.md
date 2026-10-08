## Defining a template

1. Go to **Accounting > Configuration > Accounting > Journal Entry Templates**
   and click **New**.
2. Enter the **Name**, check the **Journal** (a miscellaneous journal by
   default) and, optionally, the default **Reference** and the
   **Instructions** shown to the user.
3. Add the lines. For each line choose the **Account** (leave it empty for a
   parameter), the **Direction** and the **Amount Type**:
   - **Entered**, with a suggested **Amount** or **Formula**;
   - **Fixed**, with the **Amount**;
   - **Percentage**, with the **Percentage** and the **Base Code**;
   - **Formula**, e.g. `RENT * RATE / 100`;
   - **Balance**, at most one line per template.
4. Give the codes you use in formulas a meaningful name (e.g. `GROSS`); the
   others are filled in automatically.
5. Save. The template is checked: unknown codes, loops between formulas and
   formulas that use the balance line are refused.

On a Romanian company, the **Load Romanian Templates** button of the template
list creates the ready-made templates. The ones whose accounts are missing from
the chart of accounts are skipped; loading them again does not create
duplicates. The off-balance templates create the technical counterpart account
800000 when needed.

## Generating an entry

1. Go to **Accounting > Accounting > Entry from Template**, or click
   **Generate Entry** on a template.
2. Choose the **Template**, the **Date**, the **Reference** and, if needed, the
   **Partner**: it is set on the lines of the template that have no partner.
3. Enter the amounts. Lines with a suggested formula show the computed amount;
   switch off **Suggested** to type another amount.
4. Tick **Post the Entry** to post it immediately, or leave it as a draft.
5. Click **Generate Entry**. The journal entry opens; it can be edited like any
   other entry before posting.

Example (payroll from an external payslip): enter the gross salaries, the
income tax and, if any, the advances and garnishments. The social and health
contributions and the work insurance contribution are suggested from the gross
amount; replace them with the payslip totals when they differ.
