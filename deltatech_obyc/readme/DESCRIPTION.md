# 📦 Deltatech OBYC - Product Account Determination

## Description
This module implements an account determination mechanism inspired by SAP OBYC, allowing automatic selection of debit and credit accounts based on:

- **Transaction Key** (e.g. WRX, VAX, GBB)
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
- Automatically selects debit and credit accounts during stock moves, depending on the type of stock transition
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

The module supports the following transaction keys:

| Key | Description | Typical Accounting Impact |
|-----|-------------|---------------------------|
| WRX | Goods Receipt from Supplier (GR/IR clearing) | Debit Inventory, Credit GR/IR clearing |
| VAX | Goods Issue to Customer | Debit COGS, Credit Inventory |
| ZTR | Internal Transfer | Debit Inventory Location, Credit Inventory Location |
| GBB | Consumption (General) | Debit Expense, Credit Inventory |
| BSX | Stock Posting (positive inventory) | Debit Inventory, Credit Inventory Adjustment |
| BSM | Stock Posting (negative inventory) | Debit Inventory Adjustment, Credit Inventory |
| BSV | Change in Stock | Debit/Credit Inventory Changes |
| BSD | Supplementary Entry for Stock | Adjusts Stock Account for Valuation Areas |
| AUM | Expenditure/Income from Transfer Posting | Debit/Credit Transfer Price Differences |
| UMB | Revenue/Expense from Revaluation | Debit New Account, Credit Old Account |
| PRD | Price Differences | Debit/Credit Price Difference Account |
| KON | Consignment Liabilities | Debit Consignment Stock, Credit Consignment Vendor |
| AKO | Expense/Revenue from Consumption of Consignment | Debit Expense, Credit Revenue Account |
| KDM | Exchange Rate Differences (Open Items) | Debit/Credit Exchange Rate Difference Account |
| FR1 | Freight Clearing | Debit Inventory/Expense, Credit Accrued Freight |
| FR2 | Provision for Freight Charges | Debit Freight Expense, Credit Accrued Freight |
| FRL | External Service (Subcontracting) | Debit WIP/Inventory, Credit Subcontractor |
| GBD | Scrapping | Debit Scrap Expense, Credit Inventory |

Each transaction key can be mapped to different GL accounts based on product valuation class, valuation area, and account modifiers.

## ⚙️ Models Introduced

- **product.account.determination**: Core mapping rule
- **product.valuation.class**: Master data used to group products by accounting behavior
- **product.valuation.area**: Organizational structure influencing account determination
- **account.modifier**: Optional field used to refine selection (similar to SAP account modifier)

## 📁 How it Works

When a stock move is processed:

1. The system computes a transaction key based on the source/destination locations
2. It gathers:
  - Valuation class from product
  - Valuation area from company
  - Account modifier from picking type (if set)
3. It searches for a matching rule in `product.account.determination`
4. If found, the specified debit and credit accounts are used in the accounting entries

## 🛠️ Extensibility

- You can override the logic for transaction key computation per business scenario
- Add additional dimensions (e.g. storage location, product category) if needed
- Compatible with Odoo 17 Enterprise & Community

## 📌 Use Case Example

You can configure:

- **WRX** (Goods Receipt from supplier) → Debit Inventory, Credit GR/IR
- **VAX** (Goods Issue to customer) → Debit COGS, Credit Inventory
- **GBB** (Consumption to cost center) → Debit Expense, Credit Inventory
- **BSX** (Positive inventory adjustment) → Debit Inventory, Credit Inventory Adjustment
- **AUM** (Transfer posting differences) → Debit/Credit Transfer Price Differences
- **PRD** (Price differences) → Debit/Credit Price Difference Account

Each of these can vary by product class or warehouse (valuation area).
