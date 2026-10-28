## 19.0.1.1.2 (2026-10-28)

- Consultant sheet (readme/FISA_CONSULTANT.md) with screenshots of the dialog in the modules that
  use it. Documentation only, no module update needed.

## 19.0.1.1.1 (2026-10-23)

- The counter is hidden while `init` prepares the items: it showed "0 / 0".

## 19.0.1.1.0 (2026-10-23)

- The steps can run on the item records (`model`, without a record): the
  "Send to Carrier" dialog of `deltatech_delivery`.
- A step can return a status: `warning` is done and never run again (a result to check
  by hand), `error` is run again by the retry button.
- List of the items with their status and message (`show_items`); start button with an
  introduction (`auto_start=False`, `intro`); finish as a button on the items done
  (`finish_mode="button"`); `init` method that prepares the items when the dialog opens;
  `close` method called when the dialog is closed after a complete run.
- Development status Production/Stable: `deltatech_delivery` (stable) depends on it.

## 19.0.1.0.0 (2026-10-23)

- First version: the progress dialog of `deltatech_ai_purchase_pdf`, made generic
  through `task.progress.mixin`.
