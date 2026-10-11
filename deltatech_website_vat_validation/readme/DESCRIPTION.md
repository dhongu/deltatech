

# Deltatech Website VAT Validation

This module enhances the VAT (Value Added Tax) validation functionality on Odoo website checkout and customer portal, ensuring VAT numbers are properly validated.

## Features

- Automatic VAT number validation during website checkout
- VAT number validation in customer portal when updating details
- Prevention of duplicate VAT numbers across different customers
- Automatic trimming of whitespace from VAT entries
- Integration with both website sale checkout process and customer portal
- Clear error messages when a VAT number is already in use

The Romanian checks of the tax code (ANAF look-up, personal numeric code, struck-off company)
are in `l10n_ro_website_anaf` (l10n-romania): this module stays country-neutral.

## Benefits

- Improved data quality by preventing duplicate VAT registrations
- Enhanced compliance with tax regulations
- Better customer experience with immediate feedback on VAT number validity
- Reduced manual verification by administrators
- Streamlined checkout process with proper validation
- Prevention of potential billing and accounting issues related to incorrect VAT information
