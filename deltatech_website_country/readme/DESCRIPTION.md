eCommerce Country and Address Enhancements
==========================================

This module provides country-related extensions for Odoo's eCommerce platform. It ensures that the checkout address form always has a default country pre-selected, based on the website's company country, improving the address entry experience for customers.

Key Features
============

1.  **Country-Specific Frontend Logic**:
    *   Enhances the website checkout address form with improved country and state selection.
    *   Integrates with Odoo's base country data to ensure that address forms adapt to the chosen country's format.

2.  **Optimized Address Validation**:
    *   Provides a foundation for more advanced address validations (like city/zip mapping) when used in conjunction with other Deltatech website extensions.
    *   Reduces checkout friction by ensuring that customers only see relevant country or state options.

3.  **Cross-Module Foundation**:
    *   Acts as a standard dependency for other Romanian or region-specific website modules that require refined country handling.

Usage
=====

1.  No specific configuration is needed beyond standard Odoo country and state settings.
2.  Install the module, and the website's checkout address page will automatically pre-select the company's country when no other country can be determined.
3.  Go to **Website > Configuration > Countries** to ensure your target markets are active and correctly configured with their respective states.
