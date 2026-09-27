City Extension for Website
===========================

This module enhances the address management system in the Odoo eCommerce and Portal areas by providing structured city selection. It's particularly useful for regions where city names need to be validated or selected from a predefined list rather than being entered as free text.

Key Features
============

1.  **Structured City Selection**:
    *   Replaces the standard free-text city input with a structured selection mechanism on the website checkout and portal address pages.
    *   Integrates with the `base_address_extended` module to leverage Odoo's built-in city management.

2.  **Automatic ZIP/Postcode Mapping**:
    *   Facilitates automatic population or validation of postal codes based on the selected city.
    *   Reduces user entry errors during the checkout process, leading to better delivery accuracy.

3.  **Frontend and Portal Integration**:
    *   Provides customized JavaScript (ES modules) to handle dynamic city/ZIP interactions in the browser.
    *   Ensures a consistent address entry experience between the public website shop and the private customer portal.

Usage
=====

1.  Navigate to **Contacts > Configuration > Cities** (requires `base_address_extended`).
2.  Define the list of cities and their corresponding ZIP codes and states.
3.  Go to the website shop and proceed to the checkout address page.
4.  Users will now be able to select cities from the predefined list, and the system will assist with the corresponding address details.
