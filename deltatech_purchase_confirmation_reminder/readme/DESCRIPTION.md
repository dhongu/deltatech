Purchase Confirmation Activity Reminder
========================================

This module introduces an automated reminder system for purchase order confirmations in Odoo. It is designed to help procurement teams track pending confirmations from suppliers, ensuring that purchase orders are acknowledged and processed in a timely manner.

Key Features
============

1.  **Automated Confirmation Activities**:
    *   Automatically creates an **Activity** (Call, Email, or custom) on a Purchase Order if it hasn't been confirmed within a specified timeframe.
    *   Integrates with Odoo's core **Mail (Discuss)** and **Purchase** modules.

2.  **Configurable Reminder Rules**:
    *   Allows administrators to define the reminder threshold (number of days) and the type of activity to be created.
    *   Features a dedicated settings page for fine-tuning the reminder behavior globally.

3.  **Procurement Efficiency**:
    *   Uses a background cron job to periodically check for unconfirmed purchase orders and trigger reminders, reducing manual follow-up effort.

Usage
=====

1.  Navigate to **Purchase > Configuration > Settings**.
2.  Locate the **Purchase Confirmation Reminder** section and define the number of days for the follow-up.
3.  Create a new **Purchase Order** and send it to the supplier.
4.  If the supplier does not confirm the order within the defined timeframe, the system will automatically create an activity for the assigned procurement officer to follow up.
