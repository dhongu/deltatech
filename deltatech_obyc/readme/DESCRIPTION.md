# 📦 Deltatech OBYC - Product Account Determination

## Description
This module implements an account determination mechanism inspired by SAP OBYC (OBject-based valuation and account determination for inventorY and Cost management). It allows automatic selection of accounts based on:

- **Transaction Key** (e.g. stock_receipt, stock_delivery)
- **Valuation Class** (from the product)
- **Valuation Area** (e.g. by company, plant, warehouse)
- **Account Modifier** (from operation context)
- **Company**

## 🧩 Key Features

- Defines a flexible mapping table (`product.account.determination`) for automatic GL account assignment
- Introduces configurable master data:
  - `product.valuation.class` – assigned to product templates
  - `product.valuation.area` – assigned to companies
  - `account.modifier` – optionally used in operations (e.g., picking types)
- Automatically selects source, destination, and valuation accounts during stock moves
- Transaction key determination logic for common inventory operations

## 🔄 Transaction Key Mapping (Default Logic)

| Source Location | Destination Location | Transaction Key |
|-----------------|----------------------|-----------------|
| Supplier        | Internal            | stock_receipt    |
| Internal        | Customer            | stock_delivery   |
| Internal        | Internal            | internal_transfer |
| Customer        | Internal            | return_from_customer |
| Internal        | Supplier            | return_to_supplier |
| Supplier        | Customer            | dropship         |

You can customize the transaction key determination logic in `stock.move` to support more complex cases.

## 📋 Comprehensive Transaction Keys List

The module implements the following transaction keys:

| Key                           | Description                   | Typical Accounting Impact                            | SAP Equivalent  |
|-------------------------------|-------------------------------|------------------------------------------------------|-----------------|
| **Stock Valuation**           |
| stock_valuation               | Stock Valuation               | Debit/Credit for valuation updates                   | BSX             |
| **Purchase Transactions**     |
| stock_receipt                 | Stock Receipt from Supplier   | Debit Inventory, Credit GR/IR clearing               | WRX             |
| return_to_supplier            | Return to Supplier            | Debit GR/IR clearing, Credit Inventory               | -               |
| **Sale Transactions**         |
| stock_delivery                | Delivery to Customer          | Debit COGS, Credit Inventory                         | VAX             |
| return_from_customer          | Return from Customer          | Debit Inventory, Credit COGS                         | -               |
| stock_income                  | Income Recognition            | Debit Receivables, Credit Revenue                    | SAL             |
| **Dropshipping Transactions** |
| dropship                      | Dropshipping                  | Debit COGS, Credit Payables                          | -               |
| dropship_return               | Dropshipping Return           | Debit Payables, Credit COGS                          | -               |
| **Internal Transfers**        |
| internal_transfer             | Internal Transfer             | Debit Destination Inventory, Credit Source Inventory | ZTR             |
| internal_transfer_out         | Internal Transfer Out         | Credit Source Inventory                              | -               |
| internal_transfer_in          | Internal Transfer In          | Debit Destination Inventory                          | -               |
| **Inventory Adjustments**     |
| inventory_adjustment_plus     | Positive Inventory Adjustment | Debit Inventory, Credit Inventory Adjustment         | BSX             |
| inventory_adjustment_minus    | Negative Inventory Adjustment | Debit Inventory Adjustment, Credit Inventory         | -               |
| **Production Transactions**   |
| production_issue              | Production Consumption        | Debit WIP, Credit Raw Materials                      | -               |
| production_receipt            | Production Receipt            | Debit Finished Goods, Credit WIP                     | -               |

## ⚙️ Models Introduced

- **product.account.determination**: Core mapping rule
- **product.valuation.class**: Master data used to group products by accounting behavior
- **product.valuation.area**: Organizational structure influencing account determination
- **account.modifier**: Optional field used to refine selection (similar to SAP account modifier)

## 📁 How it Works

When a stock move is processed:

1. **Transaction Key Determination**: The system computes a transaction key based on the source/destination locations and operation type
   ```
   Example: stock_receipt for supplier receipts, stock_delivery for customer deliveries
   ```

2. **Parameters Collection**:
  - Valuation class from product (e.g., "RM" for raw materials, "FG" for finished goods)
  - Valuation area from company (e.g., "MAIN" for main company)
  - Account modifier from picking type (e.g., "STD" for standard)

3. **Rule Matching**: It searches for a matching rule in `product.account.determination`
   ```
   Search criteria: Transaction Key + Valuation Class + Valuation Area + Account Modifier + Company
   ```

4. **Account Application**: If a rule is found, the three specified accounts are used in the accounting entries:
  - **Source Account** (acc_src_id): Typically used as the credit account in transactions
  - **Destination Account** (acc_dest_id): Typically used as the debit account in transactions
  - **Valuation Account** (acc_valuation_id): Used for stock valuation and price differences


## 🧩 Account Determination Model

Each account determination rule (`product.account.determination`) contains:

1. **Transaction Key** (transaction_key): Defines the type of operation (stock_receipt, stock_delivery, etc.)
2. **Account Modifier** (account_modifier_id): Allows refinement of account selection
3. **Valuation Class** (valuation_class_id): Groups products by accounting behavior
4. **Valuation Area** (valuation_area_id): Allows different accounting per company/division
5. **Company** (company_id): The company for which the rule applies
6. **Source Account** (acc_src_id): The account used for the credit side
7. **Destination Account** (acc_dest_id): The account used for the debit side
8. **Valuation Account** (acc_valuation_id): The account used for valuation and price differences

This flexible structure allows defining complex accounting rules for various types of inventory operations.

## 🛠️ Extensibility

- You can override the logic for transaction key computation per business scenario
- Add additional dimensions (e.g., storage location, product category) if needed
- Compatible with Odoo 17 Enterprise & Community
- Extensible for adaptation to industry specifics or special accounting requirements

## 📌 Usage Examples

### Basic Configuration

To configure the module:

1. Define valuation classes for products (e.g., Raw Materials, Semi-Finished, Finished Goods)
2. Define valuation areas for companies
3. Define account modifiers (optional)
4. Configure account determination rules in `product.account.determination`

### Typical Account Mappings

| Key | Valuation Class | Source Account | Destination Account | Valuation Account | Description |
|-----|----------------|---------------|-------------------|-----------------|-------------|
| stock_receipt | RM | 408000 | 301000 | 378000 | Raw materials receipt |
| stock_receipt | FG | 408000 | 371000 | 378000 | Finished goods receipt |
| stock_delivery | FG | 371000 | 607000 | 378000 | Finished goods delivery |
| inventory_adjustment_plus | RM | 601800 | 301000 | 378000 | Positive adjustment raw materials |
| inventory_adjustment_minus | FG | 371000 | 608000 | 378000 | Negative adjustment finished goods |
| production_receipt | FG | 711000 | 371000 | 378000 | Production receipt |
| production_issue | RM | 301000 | 601000 | 378000 | Production consumption |
| internal_transfer | RM | 301000 | 301000 | 378000 | Transfer between locations |
| stock_income | FG | 707000 | 411000 | 378000 | Sales revenue posting |
| dropship | FG | 408000 | 607000 | 378000 | Direct delivery from supplier to customer |
| return_from_customer | FG | 607000 | 371000 | 378000 | Return of goods from customer |
| return_to_supplier | RM | 301000 | 408000 | 378000 | Return of goods to supplier |

Each of these mappings can vary by product class or warehouse (valuation area).

## 🔍 Comparison with SAP OBYC

This module is inspired by the SAP OBYC concept but adapted for the Odoo ecosystem. The main differences include:

- Simplification: Transaction keys are named descriptively rather than using SAP codes
- Integration: Works natively with the Odoo inventory system
- Flexibility: Allows simpler customizations than the original SAP system
- Structure: Uses concepts familiar to Odoo users (products, locations, stock moves)

## 📚 Additional Resources

- [Odoo Accounting Documentation](https://www.odoo.com/documentation/17.0/applications/finance/accounting.html)
- [Odoo Inventory Management Documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory.html)
- [SAP OBYC Reference](https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/f0a0f6a2c5534160b5af7a96ecc81d3c/3ce36768fe599c4be10000000a174cb4.html)

## 📣 Important Notes

- Ensure you understand the accounting implications before configuring this module
- Test the configuration in a test environment before using it in production
- Consult with an accounting expert to ensure compliance with local accounting regulations
- The module is compatible with Odoo 17, but can be adapted for other versions

## 🧮 Three-Account System

The key innovation of this module is the three-account system that provides enhanced flexibility for inventory accounting:

1. **Source Account** (acc_src_id): Typically represents the origin of the value (credit side)
  - For purchases: Accounts payable or GR/IR clearing
  - For sales: Inventory account
  - For internal operations: Source location's inventory account

2. **Destination Account** (acc_dest_id): Represents where the value goes (debit side)
  - For purchases: Inventory account
  - For sales: Cost of goods sold
  - For internal operations: Destination location's inventory account

3. **Valuation Account** (acc_valuation_id): Handles value differences and revaluations
  - Price differences between standard and actual costs
  - Exchange rate differences
  - Revaluation adjustments
  - Inventory valuation changes

This three-account approach enables more sophisticated accounting treatments than Odoo's standard two-account inventory valuation system, allowing businesses to:

- Track price differences separately from inventory movements
- Handle complex valuation scenarios (FIFO, LIFO, standard cost with variances)
- Support compliance with international accounting standards
- Maintain detailed audit trails for inventory value changes

## 📊 Transaction Key Use Cases

### Purchase Flow
- **stock_receipt**: When goods are received from a supplier
  - Debit: Inventory (Destination Account)
  - Credit: GR/IR Clearing (Source Account)
  - Valuation Account: Used for price differences

- **return_to_supplier**: When goods are returned to a supplier
  - Debit: GR/IR Clearing (Destination Account)
  - Credit: Inventory (Source Account)
  - Valuation Account: Used for price differences

### Sales Flow
- **stock_delivery**: When goods are delivered to a customer
  - Debit: COGS (Destination Account)
  - Credit: Inventory (Source Account)
  - Valuation Account: Used for price differences

- **return_from_customer**: When goods are returned from a customer
  - Debit: Inventory (Destination Account)
  - Credit: COGS (Source Account)
  - Valuation Account: Used for price differences

- **stock_income**: When revenue is recognized
  - Debit: Receivables (Destination Account)
  - Credit: Revenue (Source Account)
  - Valuation Account: Usually not used in this context

### Inventory Management
- **inventory_adjustment_plus**: For positive inventory adjustments
  - Debit: Inventory (Destination Account)
  - Credit: Inventory Adjustment (Source Account)
  - Valuation Account: Used for valuation effects

- **inventory_adjustment_minus**: For negative inventory adjustments
  - Debit: Inventory Adjustment (Destination Account)
  - Credit: Inventory (Source Account)
  - Valuation Account: Used for valuation effects

### Manufacturing
- **production_issue**: When materials are consumed in production
  - Debit: WIP (Destination Account)
  - Credit: Raw Materials (Source Account)
  - Valuation Account: Used for price differences

- **production_receipt**: When finished goods are received from production
  - Debit: Finished Goods (Destination Account)
  - Credit: WIP (Source Account)
  - Valuation Account: Used for price differences

### Special Cases
- **dropship**: For direct delivery from supplier to customer
  - Debit: COGS (Destination Account)
  - Credit: Payables (Source Account)
  - Valuation Account: Used for price differences

- **internal_transfer**: For transfers between locations
  - Debit: Destination Location Inventory (Destination Account)
  - Credit: Source Location Inventory (Source Account)
  - Valuation Account: Used for price differences
