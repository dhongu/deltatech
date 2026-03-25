========================
Product Reordering Limit
========================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/github-dhongu%2Fdeltatech-lightgray.png?logo=github
    :target: https://github.com/dhongu/deltatech/tree/18.0/deltatech_product_reordering_limit
    :alt: dhongu/deltatech

|badge1| |badge2|

This module adds custom reordering limits for products at the template level.

Features
========

*   Adds **Total Minimum** and **Total Maximum** fields to product templates.
*   Provides a computed field **Is Below Minimum** to quickly identify products where stock levels are below the set minimum.
*   The **Is Below Minimum** field is searchable, allowing users to filter products that need reordering.
*   Stock levels are aggregated across variants and internal locations.

Usage
=====

1. Go to **Inventory > Products > Products**.
2. Open a product template.
3. In the **Inventory** tab, set the **Total Minimum** and **Total Maximum** values.
4. Use the search filter to find products that are **Below Minimum**.

Bug Tracker
===========

Bugs are tracked on `Terrabit Issues <https://www.terrabit.ro/helpdesk>`_.
In case of trouble, please check there if your issue has already been reported.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
-------

* Terrabit
* Voicu Stefan

Maintainers
-----------

Current maintainer:

.. image:: https://github.com/VoicuStefan2001.png?size=40px
   :target: https://github.com/VoicuStefan2001
   :alt: VoicuStefan2001

This module is part of the `dhongu/deltatech <https://github.com/dhongu/deltatech/tree/18.0/deltatech_product_reordering_limit>`_ project on GitHub.

You are welcome to contribute.
