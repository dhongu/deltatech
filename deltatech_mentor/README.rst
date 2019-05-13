===========================================
Mentor Interface
===========================================
.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3


Features:
 - Permite exportul de date din Odoo pentru a fi importate in Mentor
 - Documentatia Mentor de import  din alte aplicatii: http://download.winmentor.ro/WinMentor/Documentatie/08_Structuri%20import%20din%20alte%20aplicatii/


Utilizare:
 - trebuie facuta mapare dintre categoriile de produse din Odoo si tipul contabil din mentor.
 - conturile din Odoo sunt trimise in Mentor fara zeroruile de la sfarsit
 - daca este intalat modulul l10n_ro_stock_account se determina locatia din factura
        - din locatie de citeste codul
        - DepMP este codul utilizat in cazul in care nu este determinat un alt cod de locatie


.. image:: https://apps.odoo.com/apps/modules/12.0/deltatech_mentor/conf_art1.png
    :alt: Config1
    :scale: 50 %
    :class: img img-fluid
    :align: center
.. image:: https://apps.odoo.com/apps/modules/12.0/deltatech_mentor/conf_art2.png
    :alt: Config2
    :scale: 50 %
    :class: img img-fluid
    :align: center



Pentru importul in mentor se acceseaza meniu:
MENTOR -> Intrari -> Import date din alte aplicatii.

Pentru importul facturilor de intrare se alege submeniul 'Facturi Intrare'.

.. image:: https://apps.odoo.com/apps/modules/12.0/deltatech_mentor/meniu_import.png
    :alt: meniu_import
    :scale: 50 %
    :class: img img-fluid
    :align: center

Se slecteaza "Carnet NIR" si din calea in care a fost facuta dezarhivarea fisierului exportat de Odoo.

.. image:: https://apps.odoo.com/apps/modules/12.0/deltatech_mentor/import_facturi_intrare.png
    :alt: meniu_import
    :scale: 50 %
    :class: img img-fluid
    :align: center

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

.. image:: https://apps.odoo.com/apps/modules/12.0/deltatech/logo-terrabit.png
   :alt: Terrabit
   :target: https://terrabit.ro

This module is maintained by the Terrabit.


