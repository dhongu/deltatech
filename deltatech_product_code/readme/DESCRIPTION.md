This module enhances Odoo's product management by providing advanced tools for automated internal reference generation, barcode management, and data consistency. It is designed for businesses that require strict and structured product codification across their entire catalog, including complex multi-variant products.

Features:

- **Automated Product Codification**: Automatically generates internal references (`default_code`) for products and variants based on sequences defined at the category level.
- **Configurable Product Categories**:
  - Assign specific sequences to each product category for consistent internal coding.
  - Enable or disable automatic barcode generation.
  - Define custom barcode prefixes.
  - Choose between random barcode generation or barcodes derived from the internal reference.
- **Uniqueness Enforcement**: Implements a SQL constraint to ensure that the combination of internal reference, active status, and company is unique across all products.
- **Smart Code Regeneration**:
  - Adds a "New internal code" button on both product templates and product variants forms for manual or forced updates.
  - Supports a "Force new internal code" server action to mass-update codes for selected records.
- **Duplicate Detection**: Includes a "Find Duplicate" server action accessible from the action menu in product list views (templates and variants), helping you quickly identify and resolve naming conflicts.
- **Multi-variant Support**: Fully compatible with Odoo's product variant system, ensuring that codes are correctly handled for both templates and individual variants.
- **Barcode Integration**: Seamlessly integrates with Odoo's barcode nomenclature for sanitizing and validating generated barcodes.
