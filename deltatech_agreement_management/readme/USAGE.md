## Creating an agreement

1. Navigate to **Agreement → Agreements**.
2. Click **New**.
3. Fill in:
   - **Type** — select the agreement type (determines the sequence and print template).
   - **Partner** — the counterpart company or individual.
   - **Agreement Date** — defaults to today; change if needed.
   - **Final Date** — optional expiry date.
   - **Description** — short free-text note.
   - **Currency** — defaults to the company currency.
4. While the agreement is in **Draft** and the reference shows `/`, click
   **Get number** to assign the next sequence number from the selected type.
5. Click **Set In Progress** to move the agreement to the **In Progress** state.
   Fields become read-only once the agreement leaves Draft.
6. To print the agreement, click **Print**. The report template configured on the
   agreement type is used to generate the PDF.
7. When the agreement ends, click **Close Contract** to set the state to
   **Terminated**. To reopen it, click **Set Draft**.

## Viewing agreements from a partner

On any partner form, an **Agreements** smart button (file icon) shows the number of
agreements linked to that partner. Click it to open the filtered list of agreements
for that partner.

You can also filter partners by agreement presence: in the partner list view, use
the search filter **With agreement** to show only partners that have at least one
agreement.

## Deleting agreements

Only agreements in **Draft** state can be deleted. Attempting to delete an agreement
that is In Progress or Terminated will raise a validation error.
