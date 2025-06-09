# Overview
The Deltatech Account Analytic module is a comprehensive extension for Odoo's analytic accounting system, designed to enhance the management and tracking of analytic information. Developed by Terrabit, this module provides advanced features for splitting analytic lines, especially in sales and purchase workflows, allowing for more detailed financial analysis and reporting.


# Key Features
## Analytic Line Splitting
- **Automatic Splitting**: Automatically splits sale invoice analytic lines into stock value and margin components when the deltatech_sale_commission module is installed.
- **Configuration Settings**: Adds "Split Sale Analytic" option in the Odoo settings for enabling/disabling the splitting functionality.

## Analytic Account Enhancements
- **Split Configuration**: Extends the analytic account form with additional fields:
    - "This rule is for splitting" toggle
    - "Stock Analytic Account" selection
    - "Margin Analytic Account" selection
    - "Sale team" selection for split configuration

## Integration with Other Modules
- Seamless integration with:
    - Account module
    - Analytic module
    - Sale module
    - Purchase module

## Enhanced Views and Security
- Custom views for:
    - Account analytic defaults
    - Account analytic lines
    - Analytic split templates
    - Analytic split configurations

- Additional security rules and access rights to manage analytic operations

# Technical Details
## Module Dependencies
- account
- analytic
- sale
- purchase

## Included Data Files
1. Views:
    - res_config_settings.xml
    - account_analytic_default.xml
    - account_analytic_line.xml
    - account_analytic_split_template.xml
    - account_analytic_split.xml

2. Security:
    - security.xml
    - ir.model.access.csv

## Models Extended
- account.analytic.account: Enhances the analytic account model with additional functionality for splitting and tracking
- Adds related counters and access to invoices and bills from analytic accounts

## Benefits
1. **Improved Financial Analysis**: By splitting analytic lines into stock value and margin, the module provides deeper insights into business profitability.
2. **Enhanced Reporting**: More detailed analytic information allows for better financial reporting and decision-making.
3. **Flexible Configuration**: The ability to configure splitting rules at the analytic account level provides flexibility for different business needs.
4. **Better Integration**: Seamless integration with sales and purchase workflows ensures comprehensive tracking of costs and revenues.

## Use Cases
- **Sales Margin Analysis**: Track and analyze sales margins separately from cost of goods sold.
- **Team Performance Tracking**: Associate specific analytic accounts with sales teams for performance analysis.
- **Cost Center Management**: Better allocation of costs and revenues to appropriate cost centers.
- **Profitability Analysis**: More accurate analysis of product and service profitability.
