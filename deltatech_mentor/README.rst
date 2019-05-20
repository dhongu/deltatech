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
 - Inainte de utilizare trebuie sa va asigurati ca:
    - partenerii existenti din Mentor au completat la cod extern CUI-ul
    - articolele existenete din Mentor sunt mapate cu produsele din Odoo prin codul extern
    - este facuta mapare dintre categoriile de produse din Odoo si tipul contabil din mentor
    - la fiecare locatie de stoc este completat codul de gestiune din Mentor
    - seriile de facturi definite in mentor corespund cu secventele de numere din Odoo. Programul de export extrage seria din numele documetelor si sprara seria in functie de caracterul "/".
    - sunt completate conturile la categoriile de produse si la parteneri. Conturile din Odoo sunt trimise in Mentor fara zeroruile de la sfarsit



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

.. image:: https://apps.odoo.com/apps/modules/12.0/deltatech_mentor/conf_patener.png
    :alt: Config Partener
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

Se slecteaza "Carnet NIR" si fisierul 'Facturi Intrare' din calea in care a fost facuta dezarhivarea fisierului exportat de Odoo.

.. image:: https://apps.odoo.com/apps/modules/12.0/deltatech_mentor/import_facturi_intrare.png
    :alt: meniu_import
    :scale: 50 %
    :class: img img-fluid
    :align: center

Nota:
 - Programul Mentor face doar importul de produse si parteneri, actualizarea trebuie facuta manaula in ambele sisteme.
 - Daca la export un partener nu are CUI sau un produs nu are cod se va exporta id-ul intern din Odoo


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


