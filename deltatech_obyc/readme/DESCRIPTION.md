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

Each of these can vary by product class or warehouse (valuation area).
