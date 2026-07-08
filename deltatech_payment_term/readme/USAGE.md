1. Open a payment term (**Accounting > Configuration > Payment Terms**) and click the **Create Rate** button in the header (or open the wizard directly from a sale order or an invoice's actions menu).
2. Fill in the wizard:
   - **Name** of the payment term.
   - **Type**: Percent or Fixed Amount.
   - **Advance**: the value of the first, immediate installment.
   - **Number of rates**: how many additional equal installments to generate after the advance.
   - **Rate Value**: amount per installment when Type is Fixed Amount.
   - **Day of the Month**: the day each installment falls due on.
3. Click **Apply**. The wizard builds the payment term lines automatically: the advance line plus the requested number of equal installments spaced 30 days apart, with the last line adjusted so percentages always add up to 100%.
4. If launched from an existing payment term, the new lines replace the term's current lines; if launched without a term selected, a brand new payment term is created with the given name.
