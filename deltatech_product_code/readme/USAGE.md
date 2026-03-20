To use this module, follow these steps:

### Configuration

1.  **Product Categories**:
    - Go to **Inventory > Configuration > Product Categories**.
    - Open a category and look for the **Products** section.
    - Set a **Code Sequence** to enable automatic internal reference generation for products in this category.
    - (Optional) Enable **Generate Barcode** and configure **Prefix Barcode** and **Barcode Random** settings.

### Usage

1.  **Automatic Coding**:
    - When creating a new product or variant, the **Internal Reference** (`default_code`) and **Barcode** will be automatically generated based on the category settings if left blank.

2.  **Manual Code Generation**:
    - On a **Product Template** or **Product Variant** form, use the **New internal code** button in the header to generate a new code based on the category's sequence.

3.  **Mass Code Update**:
    - In the **Products** or **Product Variants** list view, select multiple records.
    - Open the **Action** menu and select **Force new internal code** to regenerate codes for all selected items.

4.  **Finding Duplicates**:
    - In the **Products** or **Product Variants** list view, open the **Action** menu and select **Find Duplicate**.
    - The system will filter the list to show only products that share the same internal reference (considering active status and company).
