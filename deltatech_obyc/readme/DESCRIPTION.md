# 📦 Deltatech OBYC - Product Account Determination

## Description
This module implements an account determination mechanism inspired by SAP OBYC (OBject-based valuation and account determination for inventorY and Cost management). It allows automatic selection of accounts based on:

- **Transaction Key** (e.g. WRX, VAX, BSX)
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
| Supplier        | Internal            | WRX             |
| Internal        | Customer            | VAX             |
| Internal        | Internal            | ZTR             |
| Other           | Other               | GBB (default)   |

You can customize the `_compute_transaction_key()` method in `stock.move` to support more complex cases (e.g. subcontracting, scrapping, manufacturing).

## 📋 Comprehensive Transaction Keys List

The module supports the following transaction keys adapted from SAP:

| Key | Description | Typical Accounting Impact | Use Case |
|-----|-------------|---------------------------|----------|
| WRX | Goods Receipt from Supplier | Debit Inventory, Credit GR/IR clearing | Receipt of goods against purchase order |
| VAX | Goods Issue to Customer | Debit COGS, Credit Inventory | Delivery of goods to customer against sales order |
| ZTR | Internal Transfer | Debit Destination Inventory, Credit Source Inventory | Transfer between warehouses or stock locations |
| GBB | Consumption (General) | Debit Expense, Credit Inventory | Internal consumption, usage for cost centers |
| BSX | Stock Posting (positive inventory) | Debit Inventory, Credit Inventory Adjustment | Inventory with surplus, entries without order |
| BSM | Stock Posting (negative inventory) | Debit Inventory Adjustment, Credit Inventory | Inventory with shortage, exits without order |
| AUM | Expenditure/Income from Transfer Posting | Debit/Credit Transfer Price Differences | Transfer between materials with different prices |
| PRD | Production Receipt | Debit Finished Goods, Credit WIP | Completion of production order |
| PRC | Production Consumption | Debit WIP, Credit Raw Materials | Consumption of materials for production orders |
| UMB | Revenue/Expense from Revaluation | Debit New Account, Credit Old Account | Accounting reclassification of stocks |
| GBD | Scrapping | Debit Scrap Expense, Credit Inventory | Scrapping defective or expired products |
| KON | Consignment Liabilities | Debit Consignment Stock, Credit Consignment Vendor | Management of consignment stocks |
| BSV | Change in Stock | Debit/Credit Stock Changes | Periodic stock valuation |
| FR1 | Freight Clearing | Debit Inventory/Expense, Credit Accrued Freight | Management of freight costs at reception |
| FR2 | Provision for Freight Charges | Debit Freight Expense, Credit Freight Provision | Accrual of estimated freight costs |
| SAL | Sales Invoice | Debit Receivables, Credit Revenue | Revenue posting for sales invoices |

## ⚙️ Models Introduced

- **product.account.determination**: Core mapping rule
- **product.valuation.class**: Master data used to group products by accounting behavior
- **product.valuation.area**: Organizational structure influencing account determination
- **account.modifier**: Optional field used to refine selection (similar to SAP account modifier)

## 📁 How it Works

When a stock move is processed:

1. **Transaction Key Determination**: The system computes a transaction key based on the source/destination locations
   ```
   Example: WRX for supplier receipts, VAX for customer deliveries
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

1. **Transaction Key** (transaction_key): Defines the type of operation (WRX, VAX, BSX, etc.)
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

| Key | Valuation Class | Valuation Area | Source Account | Destination Account | Valuation Account | Description                        |
|-----|-----------------|----------------|----------------|---------------------|-------------------|------------------------------------|
| WRX | RM              | MAIN           | 408000         | 408000              |                   | Raw materials receipt              |
| WRX | FG              | MAIN           | 408000         | 408000              |                   | Finished goods receipt             |
| VAX | FG              | MAIN           | 607000         | 607000              |                   | Finished goods delivery            |
| BSX | RM              | MAIN           |                |                     | 301000            | Positive adjustment raw materials  |
| BSM | FG              | MAIN           |                |                     | 378000            | Negative adjustment finished goods |
| PRD | FG              | MAIN           | 711000         | 371000              | 378000            | Production receipt                 |
| PRC | RM              | MAIN           | 601000         | 601000              |                   | Production consumption             |
| AUM | RM              | MAIN           | 408000         | 301000              | 378000            | Transfer with price difference     |
| SAL | FG              | MAIN           | 707000         | 707000              |                   | Sales revenue posting              |
| GBB | FG              | MAIN           | 601000         | 601000              |                   | Consumption                        |

Each of these mappings can vary by product class or warehouse (valuation area).

## 🔍 Comparison with SAP OBYC

This module is inspired by the SAP OBYC concept but adapted for the Odoo ecosystem. The main differences include:

- Simplification: Only essential transaction keys for most business scenarios are implemented
- Integration: Works natively with the Odoo inventory system
- Flexibility: Allows simpler customizations than the original SAP system
- Structure: Uses concepts familiar to Odoo users (products, locations, stock moves)

## 📚 Additional Resources

- [SAP OBYC Documentation](https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/f0a0f6a2c5534160b5af7a96ecc81d3c/3ce36768fe599c4be10000000a174cb4.html)
- [Odoo Accounting Documentation](https://www.odoo.com/documentation/17.0/applications/finance/accounting.html)
- [Odoo Inventory Management Documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory.html)

## 📣 Important Notes

- Ensure you understand the accounting implications before configuring this module
- Test the configuration in a test environment before using it in production
- Consult with an accounting expert to ensure compliance with local accounting regulations
- The module is compatible with Odoo 17, but can be adapted for other versions

## 🧮 Three-Account System

The key innovation of this module is the three-account system that provides enhanced flexibility for inventory accounting:

1. **Source Account**: Typically represents the origin of the value (credit side)
  - For purchases: Accounts payable or GR/IR clearing
  - For sales: Inventory account
  - For internal operations: Source location's inventory account

2. **Destination Account**: Represents where the value goes (debit side)
  - For purchases: Inventory account
  - For sales: Cost of goods sold
  - For internal operations: Destination location's inventory account

3. **Valuation Account**: Handles value differences and revaluations
  - Price differences between standard and actual costs
  - Exchange rate differences
  - Revaluation adjustments
  - Inventory valuation changes

This three-account approach enables more sophisticated accounting treatments than Odoo's standard two-account inventory valuation system, allowing businesses to:

- Track price differences separately from inventory movements
- Handle complex valuation scenarios (FIFO, LIFO, standard cost with variances)
- Support compliance with international accounting standards
- Maintain detailed audit trails for inventory value changes
