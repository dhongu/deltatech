# Changelog

## 18.0.1.1.0

- Refactor the `qweb-prn` report handler and export `buildPrnUrl` so a
  companion module can intercept the report (with a lower handler sequence) and
  print through **Zebra Browser Print**, falling back to the legacy `.prn`
  download handled here. No functional change to the legacy flow.
- The whole Zebra Browser Print feature (the SDK, the enable switch and the
  print logic) lives in a separate companion module; this module stays free of
  any proprietary code and any Browser Print dependency.
