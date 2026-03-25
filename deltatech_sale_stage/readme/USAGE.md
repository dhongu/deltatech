## Setting Up Phases

1. Go to **Sales → Configuration → Sale Order Phases**.
2. Click **New** to create a phase.
3. Fill in:
   - **Name**: e.g., *Confirmed*, *Prepared*, *Shipped*, *Delivered*
   - **Sequence**: controls the order in which phases progress (lower = earlier)
   - **Color**: choose a color to visually distinguish the phase in list views
   - **Flags**: check the appropriate flag(s) that describe this phase (e.g., *Confirmed*, *Shipped*, *Delivered*, *Cancelled*)
   - **Server Action** *(optional)*: select an action to run automatically when an order enters this phase
4. Save. Repeat for each phase in your fulfillment process.

---

## Assigning a Phase to a Delivery Operation Type

To automatically advance the sale order phase when a delivery is validated:

1. Go to **Inventory → Configuration → Operations Types**.
2. Open the relevant operation type (e.g., *Delivery Orders*).
3. In the **Phase** field, select the phase that should be applied when a delivery of this type is completed.
4. Save.

From now on, when a delivery of that type is validated, the linked sale order will automatically move to the selected phase.

---

## Viewing and Changing the Phase on a Sale Order

- The current phase is displayed as a **colored badge** on each sale order in the list view and on the order form.
- To change the phase manually, open the sale order form and update the **Phase** field.
- Changing the phase to one marked as *Confirmed* will automatically confirm a draft order.
- Changing the phase to one marked as *Cancelled* will automatically cancel the order.

---

## Filtering and Grouping by Phase

In the sale orders list view:

- Use the **Search** bar → **Phase** to filter orders by a specific phase.
- Use **Group By → Phase** to organize orders by their current phase.

---

## Automatic Phase Transitions

The following events trigger automatic phase changes (no manual action required):

| Event | Phase applied |
|---|---|
| Quotation sent to customer | Phase flagged as *Send Email* |
| Order confirmed | Phase flagged as *Confirmed* |
| Order invoiced | Phase flagged as *Invoiced* |
| Order cancelled | Phase flagged as *Cancelled* |
| Delivery validated (by operation type) | Phase assigned on the operation type |
| Courier picks up parcel / in transit | Phase flagged as *Shipped* |
| AWB generated | Phase flagged as *Pre-advice* |
| Parcel delivered to customer | Phase flagged as *Delivered* |
| Parcel refused by customer | Phase flagged as *Refused* |
