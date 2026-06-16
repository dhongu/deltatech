# Zebra Browser Print SDK

This folder must contain the **Zebra Browser Print JavaScript SDK**, which is
proprietary and distributed by Zebra on a by-request basis. It is **not**
committed to this repository.

## How to enable Browser Print on an instance

1. Download the Browser Print SDK and the desktop service from Zebra:
   <https://www.zebra.com/us/en/support-downloads/software/printer-software/browser-print.html>
2. Take the SDK script (e.g. `BrowserPrint-3.1.250.min.js`), rename it to
   **`BrowserPrint.min.js`** and drop it in this folder
   (`deltatech_report_prn/static/lib/zebra/BrowserPrint.min.js`).
3. Install the Browser Print **desktop service** on each workstation that
   prints labels (Windows/macOS installer from the same page). This replaces
   the legacy `.prn` file association + `.bat` script.
4. In Odoo, enable **Settings → General Settings → Integrations → Zebra Browser
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
