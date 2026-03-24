=========================
eCommerce Warehouse Stock
=========================

The **eCommerce Warehouse Stock** module provides a way to display stock availability across different warehouses directly on your Odoo website's product page. This information helps customers see which locations have the items they need, improving their shopping experience.

Configuration
=============

1. Go to **Website** > **Configuration** > **Settings**.
2. Find the **Warehouse Stock** section.
3. Set the **Website Warehouse Stock Threshold**.
   * This value determines when to show "Available" instead of the exact quantity. For example, if set to 10, any stock greater than 10 will be shown as "Available".
4. To enable or disable stock display for a specific warehouse:
   * Go to **Inventory** > **Configuration** > **Warehouses**.
   * Open the warehouse record.
   * Under the **Technical Information** or **Website** tab, toggle the **Display on Website** checkbox.

Usage
=====

Displaying Stock on Product Pages
---------------------------------

1. Once configured, a new section will appear on the product page in the eCommerce store.
2. This section lists all warehouses that have **Display on Website** enabled.
3. For each warehouse, the system calculates the available quantity (Physical Qty - Outgoing Qty) and displays:
   * **Available**: If the quantity is above the configured threshold.
   * **Exact Quantity**: If the quantity is between 1 and the threshold.
   * **Out of stock**: If the quantity is 0 or less.

.. image:: https://apps.odoocdn.com/apps/assets/17.0/deltatech_website_warehouse_stock/stock_warehouse.png
   :align: center
   :alt: Warehouse Stock on Product Page

Settings Overview
-----------------

1. You can adjust the threshold at any time in the Website settings.
2. Changes to warehouse visibility are immediate; unchecking **Display on Website** for a warehouse will remove it from all product pages instantly.

.. image:: https://apps.odoocdn.com/apps/assets/17.0/deltatech_website_warehouse_stock/settings.png
   :align: center
   :alt: Website Configuration Settings
