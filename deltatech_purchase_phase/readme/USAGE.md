1. Go to **Purchase > Configuration > Purchase Order Phases** and make sure the
   phases you need exist (each has a unique **Code**, e.g. `draft`, `rfq`,
   `purchase_confirm`, `done`, and a human-readable **Name**).
2. Open any Purchase Order: the **Phase** field is shown on the form and can be
   set manually at any time. Changes are tracked in the chatter.
3. The phase also updates automatically:
   - when the RFQ is sent, the phase is set to the phase with code `rfq`;
   - when the order is confirmed, the phase is set to the phase with code
     `purchase_confirm`.
   - If the referenced phase code does not exist yet, it is created on the fly.
4. You can still override the phase manually afterwards.
5. For data imports or scripted flows where the automatic update is not
   wanted, pass the context key `{"skip_phase_update": True}` when writing on
   `purchase.order`.
