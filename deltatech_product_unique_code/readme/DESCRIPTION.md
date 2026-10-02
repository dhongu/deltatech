Features:

 - Restricts the use of duplicate Internal Reference (default_code) and Barcode in products.
 - The uniqueness check includes archived products to prevent reusing codes from old records.
 - Validation is performed on both product templates and product variants.
 - Only values that actually change are validated ("no new duplicates" policy): products that
   already carry a historical duplicate can still be cleaned up (archived, corrected one field
   at a time, code cleared or renamed) by regular users — but any new or changed value must be
   unique.
 - Includes a security group "Product Duplicate Code" to allow specific users to bypass these restrictions if necessary.
