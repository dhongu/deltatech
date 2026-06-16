# Zebra Browser Print SDK

This folder must contain the **Zebra Browser Print JavaScript SDK**, which is
proprietary and distributed by Zebra on a by-request basis. It is **not**
committed to this repository.

## How to provide the SDK

The SDK url is read from the `deltatech_report_prn.browser_print_sdk_url` system
parameter (default: `/deltatech_report_prn/static/lib/zebra/BrowserPrint.min.js`).
There are two supported ways to provide it:

- **Recommended — private companion module.** Ship the SDK in a private module
  (e.g. `deltatech_report_prn_zebra_sdk` in the private `bitshop_ent` repo) and
  let it set the system parameter to its own static path. This keeps this public
  AGPL module free of proprietary code. Nothing to drop here.
- **Standalone** — drop the SDK in this folder. Take the script from Zebra (e.g.
  `BrowserPrint-3.1.250.min.js`), rename it to **`BrowserPrint.min.js`** and
  place it here. It is git-ignored on purpose (see the repo root `.gitignore`).

Download the SDK and the desktop service from Zebra:
<https://www.zebra.com/us/en/support-downloads/software/printer-software/browser-print.html>

## How to enable Browser Print on an instance

1. Provide the SDK (companion module or standalone, see above).
2. Install the Browser Print **desktop service** on each workstation that
   prints labels (Windows/macOS installer from the same page). This replaces
   the legacy `.prn` file association + `.bat` script.
3. In Odoo, enable **Settings → General Settings → Integrations → Zebra Browser
   Print**.

## Behaviour

- If the setting is **off** (default), labels are downloaded as a `.prn` file
  and handled by the legacy workstation flow. Nothing changes.
- If the setting is **on** but this SDK file is missing, or the Browser Print
  service is not running on the workstation, or no printer can be resolved, the
  module **automatically falls back** to the legacy `.prn` download. This is why
  the SDK is loaded lazily and kept out of the manifest assets — instances
  without it still build and work.

The JS that consumes this SDK lives in
`deltatech_report_prn/static/src/js/action_manager.esm.js`.
