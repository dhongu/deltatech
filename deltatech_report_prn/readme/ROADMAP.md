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

### Phase 1 — Browser Print transport (MVP) — DONE in 18.0.1.1.0

- [x] Master switch in **Settings → General Settings → Integrations → Zebra
      Browser Print** (`ir.config_parameter`
      `deltatech_report_prn.browser_print_enabled`, default off), exposed to the
      web client via `session_info` (`ir_http.py`).
- [x] Keep the proprietary SDK **out** of this public module entirely. It is
      provided by a separate (private) companion module that loads it via
      `web.assets_backend` as the global `window.BrowserPrint`; this module just
      checks for that global and keeps no SDK path or reference.
- [x] Extend the `qweb-prn` handler in `action_manager.esm.js`: when the switch
      is on, `fetch` the rendered ZPL text (reuse the existing `/report/prn/...`
      route) and send it via `device.send(zpl, success, error)` instead of
      `download()`.
- [x] Surface success/error to the user via Odoo notifications.
- [x] Graceful fallback to the legacy `.prn` download when the switch is off,
      no companion module provides the SDK, the Browser Print service is
      unreachable, or no printer can be resolved — so existing instances and
      mixed fleets keep working unchanged.

### Phase 2 — Printer discovery and selection

Discovery happens **on the workstation** via the Browser Print JS SDK
(`BrowserPrint.getLocalDevices(success, error, "printer")` and
`BrowserPrint.getDefaultDevice("printer", ...)`), never on the server — which
is what makes it work on Odoo.sh. Each discovered device exposes `name`, `uid`,
`connection` (`usb` / `network` / `driver`) and `manufacturer`.

**Design decision — persist the printer choice per workstation, NOT per user.**
The device `uid` is specific to the machine; storing it on `res.users` would
break the moment a user prints from a different computer (the saved `uid` does
not exist there). The chosen printer belongs to the machine, so it is persisted
machine-locally.

Selection cascade (first match wins):

- [ ] Saved selection on **this workstation** via `localStorage`
      (`zebra_printer_uid`, or `zebra_printer_uid:<user_id>` if different users
      on the same machine need different printers). Not a field on `res.users`.
- [ ] The Browser Print **default device** configured once per machine in the
      Zebra desktop app (`getDefaultDevice`) — survives user change, browser
      change and Odoo restarts. This is the recommended "set & forget" path.
- [ ] Auto-select when discovery returns exactly one printer.
- [ ] Otherwise show an OWL dialog to pick a printer, then persist the chosen
      `uid` to `localStorage` (back to the first step).

- [ ] Optional defensive filter to keep only Zebra/ZPL printers
      (`manufacturer` matches `zebra`, or two-way `~HQES` status probe).
- [ ] Settings flag to enable/disable Browser Print globally (so customers can
      migrate gradually while keeping the `.bat` fallback).

The optional `zebra.printer` model, if added, is for friendly names / logical
labels (e.g. "reception printer") — **not** for binding a `uid` to a user. The
physical `uid -> workstation` mapping stays in `localStorage` / the machine's
default device.

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
