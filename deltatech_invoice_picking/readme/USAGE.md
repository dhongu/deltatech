1. On a Sale Order form, the **Force Invoice Order** field (next to Fiscal Position) can be enabled if you want to invoice from the order directly instead of from pickings.
2. Deliver the goods normally. Once a stock picking coming from a sale order or a purchase order is validated (state **Done**), it is automatically flagged **To Invoice**.
3. Open the picking (Inventory > Transfers) or select several pickings from the list view. An **Invoice** button appears on sale-related pickings and a **Bill** button on purchase-related pickings, visible only when the picking is done and still marked to invoice.
4. From the picking list view you can also select multiple pickings and use the **Create Sale Invoices** / **Create Purchase Invoices** actions (Action menu) to invoice them together — only the delivered/received quantities on the selected pickings are added to the invoice.
5. Pickings grouped in a batch (Inventory > Transfers > Batch Transfers) show the same **Invoice** button on the batch form, so all their sale orders can be invoiced at once.
6. Use the **To invoice** filter in the picking search view to quickly find pickings still pending invoicing.
7. On the picking form, the **Invoice** field shows the invoice generated from that picking (read-only link), and for purchase receipts a **Supplier Invoice Number** field is available.
8. On the resulting invoice/bill, the **From Pickings** field (Other Info tab) lists the source pickings for traceability.
9. Note: if you later edit the invoice (delete lines, change quantities), the linked pickings are not automatically updated to reflect those changes.
