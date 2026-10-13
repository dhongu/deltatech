Sale Order Activity Search Extension
====================================

This module enhances the search and filtering capabilities of the Sales module in Odoo by providing more visibility into active activities associated with sales orders. It's designed to help sales teams and managers quickly identify and track orders that require immediate attention or have specific types of pending tasks.

Key Features
============

1.  **Activity Type Visibility**:
    *   Adds a technical field to the Sales Order model that stores the types of active (pending) activities for each order.
    *   Allows users to see at a glance which orders have "Call", "Email", "Meeting", or custom activity types scheduled.

2.  **Enhanced Searching and Filtering**:
    *   Provides specialized search filters to find sales orders based on their active activity types.
    *   Improves the efficiency of follow-up processes by allowing sales teams to prioritize orders based on their scheduled tasks.

3.  **Cross-Module Integration**:
    *   Seamlessly integrates Odoo's core **Sales** and **Mail (Discuss)** modules.

Usage
=====

1.  Navigate to **Sales > Orders**.
2.  Schedule one or more activities (e.g., Call, Email) on several sales orders.
3.  Use the search bar and its filtering options to find orders with specific pending activity types.
4.  The system will dynamically update the visibility of these orders based on their active scheduled tasks.
