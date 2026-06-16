# Roadmap: Zebra Browser Print integration

## Background

Today this module renders Zebra labels as **ZPL text** through the `qweb-prn`
report type (`ir.actions.report._render_qweb_prn`) and the frontend handler in
`static/src/js/action_manager.esm.js` triggers a **download of a `.prn` file**.
On each workstation that `.prn` extension is associated with a `.bat` script
that forwards the file to the printer.

This flow has known limitations:

- The `.bat` file and the file-extension association must be configured on
  **every** workstation — hard to maintain across many customers.
- Browsers increasingly block or warn about auto-opening downloaded files; the
  association breaks on browser/OS updates and on new Windows profiles.
- No feedback to the user when printing fails.

## Deployment constraint: Odoo.sh

The production environment runs on **Odoo.sh**. The application server is hosted
in Odoo's cloud and has **no route to the customer's local network**, so a
server-side raw socket to a printer (TCP port `9100`) is **not viable** — it
would only work for printers with a public IP, which is insecure and excluded.

Consequence: the print transport must originate **from the workstation** (the
browser), because the workstation is the only host on the same LAN as the
printer. This is also why the current `.bat` download flow works on Odoo.sh at
all — it is already client-side.

## Goal

Replace the `.prn` download + `.bat` association with **Zebra Browser Print**,
keeping the existing ZPL generation untouched. Browser Print covers **both USB
and network printers** because it runs as a local service on the workstation
and auto-discovers Zebra printers on USB and on the local network.

Reference: <https://www.zebra.com/us/en/support-downloads/software/printer-software/browser-print.html>

## Architecture decision

- **Transport:** Zebra Browser Print only. No server-side TCP, no IoT Box
  (customers are on Community, not Enterprise).
- **ZPL generation:** unchanged — keep `_render_qweb_prn` and the QWeb label
  templates. Only the delivery step changes (fetch the rendered text instead of
  downloading a file).
- **Per-workstation prerequisite:** the Zebra Browser Print **service** is
  installed once on each workstation (Windows/macOS installer from Zebra). The
  Browser Print **JavaScript SDK** is bundled inside this module's assets, not
  downloaded per customer.

## Phases

### Phase 1 — Browser Print transport (MVP)

- [ ] Bundle the Zebra Browser Print JS SDK (`BrowserPrint-*.min.js`) under
      `static/lib/zebra/` and register it in `web.assets_backend`.
- [ ] Extend the `qweb-prn` handler in `action_manager.esm.js`: when Browser
      Print is enabled, `fetch` the rendered ZPL text (reuse the existing
      `/report/prn/...` route, content type `text`) instead of calling
      `download()`, then send it via `device.send(zpl, success, error)`.
- [ ] Surface success/error to the user via Odoo notifications (the missing
      feedback of the current flow).
- [ ] Graceful fallback: if the Browser Print service is not reachable on
      `localhost`, fall back to the existing `.prn` download so nothing breaks
      during rollout.

### Phase 2 — Printer selection and defaults

- [ ] Optional `zebra.printer` model to register named printers and a default
      printer per user (`user_ids`) and per company (`company_id`).
- [ ] Settings flag to enable/disable Browser Print globally (so customers can
      migrate gradually while keeping the `.bat` fallback).
- [ ] Let the user pick a printer when Browser Print discovers more than one
      device; remember the last used one.

### Phase 3 — Rollout and decommissioning

- [ ] Document the one-time Browser Print service install for end users
      (Windows + macOS), replacing the `.bat` + extension-association setup.
- [ ] Migrate customers workstation by workstation, keeping the `.prn`
      fallback active until all are switched over.
- [ ] Once a customer is fully migrated, remove the `.bat` association from
      their workstations.

## Out of scope (future)

- **Unattended / automatic printing** (e.g. auto-print on stock validation when
  no browser session is open) cannot be served by Browser Print, which needs an
  active page. That requires a cloud print relay such as **PrintNode** (a local
  PrintNode client polls the cloud; Odoo.sh pushes jobs via its API). Track this
  separately if the need arises.
