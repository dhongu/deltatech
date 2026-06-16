# Changelog

## 18.0.1.1.0

- Add optional **Zebra Browser Print** transport for `qweb-prn` reports,
  gated by a configuration switch (**Settings → General Settings →
  Integrations → Zebra Browser Print**), default off.
- When enabled, the rendered ZPL/PRN text is sent directly to the printer
  through the Browser Print service on the workstation (USB or network).
- Printer selection is persisted per workstation (localStorage), with a
  cascade: saved selection → machine default device → single printer. The
  multi-printer picker dialog is planned for a later release.
- Graceful fallback: when the switch is off, or Browser Print / a printer is
  unavailable, the legacy `.prn` download flow is used, so existing instances
  and mixed fleets keep working unchanged.
- The Browser Print SDK is proprietary and not bundled here. It is provided by
  a separate (private) companion module that loads it via `web.assets_backend`
  as the global `window.BrowserPrint`; this module keeps no reference to the
  SDK and just uses the global when present.
