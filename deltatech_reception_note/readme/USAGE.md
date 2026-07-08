This module adds a **Type** field (Normal / RFQ Only / Reception Note) to Purchase Orders, plus a menu **Purchase > Reception notes** with three lists:

- **Prepare reception note**: create a purchase order of type "Reception Note" for goods that already arrived without a matching RFQ. Optionally check **Ignore quantities** to force reception of quantities larger than what is on the linked RFQs, and fill in **Delivery Note No** for the supplier's document reference.
- **To arrive**: incoming stock transfers still in "Reserved" state.
- **To invoice**: incoming stock transfers already done, pending invoicing.

Typical flow:

1. Open a confirmed/sent **Purchase Order** that was not fully received.
2. From the form view's **Action** menu, run **Create reception note**. Confirm the wizard.
3. This creates a new purchase order of type **RFQ Only** containing only the not-yet-received quantities, keeps it in "Sent" state, and cancels the original order's reserved (assigned) incoming transfers.
4. When the goods actually arrive, create a **Reception Note** order (menu above) for that partner; confirming it automatically deducts the received quantities from the matching **RFQ Only** orders, so remaining outstanding quantities stay tracked.
