The **Sale Order Return Cause** module enhances Odoo's sales management by providing a systematic way to track and analyze the reasons behind sales returns. It allows businesses to categorize returns, monitor return values, and generate insightful reports to identify and address common issues in the sales or fulfillment process.

Features
========

* **Return Cause Tracking**: Easily assign a predefined reason for each return directly on the Sale Order. Reasons include quality issues, shipping errors, client mistakes, and more.
* **Automatic Return Amount Calculation**: The module can automatically calculate the total returned value by summing up the posted credit notes related to the Sale Order invoices.
* **Return Date Logging**: Automatically records the date when a return cause is first assigned to an order.
* **Daily Automated Updates**: A scheduled action (cron) runs daily to re-verify and update return amounts for orders within the last year, ensuring data accuracy.
* **Integrated Reporting**:
    * **Sales Analysis Integration**: Return causes are integrated into the standard Sales Analysis report.
    * **Pivot & Graph Views**: Analyze return trends by cause, date, or other sales dimensions.
* **Flexible Configuration**: Choose between automatic calculation of return amounts or manual entry based on your business needs.
