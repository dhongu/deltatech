===========================================
Invoice Number
===========================================
.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3


Functions:
 - At the validation, the invoice date must be greater than the last invoice validated
 - The number of the invoice can be modified
 - A number can be allocated to a invoice in the draft state. After the number is allocated, the date of the invoice cannot be changed
 - The user must be in the account.group_account_invoice group (Accounting & Finance / Billing)

Functionalitati:
 - Validare data factura sa fie mai mare decat data din ultima factura
 - Posibilitatea de a modifica numarul unei facturi pentru un anumit grup de utilizatori
 - posibilitatea de a numerota o factura chiar daca aceasta nu este validata. Dupa numerotare nu se mai poate modifca data


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/dhongu/deltatech/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======


Contributors
------------

* Dorin Hongu <dhongu@gmail.com>


Maintainer
----------

.. image:: https://terrabit.ro/images/logo-terrabit.png
   :alt: Terrabit
   :target: https://terrabit.ro

This module is maintained by the Terrabit.


