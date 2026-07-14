# Changelog

## [18.0.1.0.9] - 2026-07-14

### Fixed
- **Bug**: the `res.currency._convert()` override made `company` and `date` required positional arguments, unlike the base method signature (`company=None, date=None`). Any core/other-module code calling `_convert()` without those two arguments (e.g. `purchase_stock`'s `_prepare_account_move_line`, when creating a vendor bill) raised `TypeError: _convert() missing 2 required positional arguments: 'company' and 'date'` whenever this module was installed alongside it. Restored the original defaults; the custom `currency_rate`-based conversion logic is unchanged.
