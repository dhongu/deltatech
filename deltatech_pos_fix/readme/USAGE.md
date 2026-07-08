This module works automatically once installed; there is no configuration or manual action needed.

It corrects a calculation issue in Point of Sale: when a product's tax is set to "tax included" but a fiscal position maps it to a different tax that is not included (for example a 0% reverse-charge tax), the POS now recalculates the unit price down to the tax-excluded amount, matching how the Sales app already behaves. The fix applies both while ringing up the sale in the POS interface and when an invoice is generated afterwards from a POS order, so totals stay consistent end-to-end.
