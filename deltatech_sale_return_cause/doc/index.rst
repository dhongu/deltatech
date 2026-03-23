======================
Sale Order Return Cause
======================

The **Sale Order Return Cause** module provides a structured approach to managing and analyzing reasons for sales returns. By assigning specific causes and tracking return amounts, businesses can gain valuable insights into product quality, shipping accuracy, and customer satisfaction.

Configuration
=============

1. Go to **Settings** > **Technical** > **Parameters** > **System Parameters**.
2. Search for the parameter `deltatech_sale_return_cause.auto_calculate`.
3. Set the value to `True` to enable automatic calculation of return amounts, or `False` to update the **Return Amount** field manually.
    * If enabled, the system will automatically sum all posted credit notes related to the Sale Order invoices.

Usage
=====

Assigning a Return Cause
------------------------

1. Open a **Sale Order**.
2. In the order details, find the **Return Cause** field.
3. Select the appropriate reason from the dropdown (e.g., *Not satisfied with quality*, *Wrongly shipped warehouse*, etc.).
4. The **Return Cause Date** will be automatically set to the current date if it was previously empty.

Monitoring Return Amounts
-------------------------

1. The **Return Amount** field on the Sale Order will display the total value of returns.
2. If auto-calculation is enabled, this field is read-only and updated whenever credit notes are processed or during the daily automated check.
3. The automated process checks all orders from the last 365 days that have a return cause assigned.

.. image:: https://apps.odoocdn.com/apps/assets/17.0/deltatech_sale_return_cause/sale_order_return_fields.png
   :align: center
   :alt: Return Fields on Sale Order

Analysis and Reporting
----------------------

1. Navigate to **Sales** > **Reporting** > **Sales**.
2. Use the **Group By** feature to organize data by **Return Cause** or **Return Cause Date**.
3. Use the **Pivot** or **Graph** view to visualize trends and identify high-frequency return reasons.

.. image:: https://apps.odoocdn.com/apps/assets/17.0/deltatech_sale_return_cause/sale_analysis.png
   :align: center
   :alt: Sales Return Analysis
