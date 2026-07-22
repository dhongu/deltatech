This module enhances the management of Bills of Materials (BoM) in Odoo by introducing a template-based approach for product variants. It streamlines the creation and maintenance of complex BoMs by allowing users to define a "Base" structure that automatically propagates to specific variants, ensuring consistency and reducing manual configuration.

- Features:

- **Enhanced Bill of Materials (BoM) Categorization**: Adds a `Base Type` field to BoMs with three options:
  - `Normal`: Standard Odoo BoM behavior.
  - `Base`: Acts as a master template for a product template, defining the general structure of components.
  - `Derived`: Specialized BoMs for specific product variants that inherit and adapt their structure from a `Base` BoM.
- **Automated Component Synchronization**: For BoMs marked as `Derived`, a "Recompute Components" button allows synchronizing components from the `Base` BoM of the same product template.
  - The system automatically identifies the correct variant for each component by matching attributes between the main product and the component's template.
- **Manufacturing Order Integration**:
  - When creating a Manufacturing Order, selecting a product variant automatically triggers the creation (if not present) and computation of a `Derived` BoM based on the existing `Base` BoM.
  - A **"Compute Derived BoM"** button is available in the Manufacturing Order (draft state) to manually trigger the creation and calculation of the derived BoM from the base BoM.
  - The derived BoM is automatically assigned a reference (code) in the format `DX` (e.g., D1, D2), where X represents the variant version number for the product template.
  - Before confirming a Manufacturing Order, the system recomputes the `Derived` BoM to ensure that all component variants are correctly selected according to the latest attribute configurations.
- **Improved Navigation**: Adds an "Open BoM" button directly on BoM lines, providing instant access to the sub-BoM of any component, which is particularly useful for complex, multi-level manufacturing structures.
- **Attribute Persistence**: Ensures that attribute values on BoM lines remain synchronized when the main product template is changed, maintaining data integrity during configuration updates.
