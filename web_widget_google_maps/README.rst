===========================================
Widget Google Maps
===========================================
.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3


It offers the functionality of editing locations and routes on the goolge map
 1. Location - Allows you to display and edit a marker on the google map: *<widget name="gmap_marker" lat="field_lat" lng="field_lng" />*
 2. Route - Allows you to display routes on the google map: *<widget name="gmap_route" from_lat="field_from_lat" from_lng="field_from_lng" to_lat="field_to_lat" to_lng="field_to_lng"/>*
 3. Locations - Allows you to display a list of locations on the google map


.. code::

    <record id='view_crm_partner_gmap' model='ir.ui.view'>
        <field name="name">res.partner.gmap</field>
        <field name="model">res.partner</field>
        <field name="type">gmaps</field>
            <field name="arch" type="xml">
            <field name="partner_latitude"/>
            <field name="partner_longitude"/>
            <field name="name"/>
            <widget name="gmap_marker" lat="partner_latitude" lng="partner_longitude" description="name"/>
        </field>
    </record>



For example see: deltatech_partner_gmap

google_maps_api_key = request.env['ir.config_parameter'].sudo().get_param('google_maps_api_key')

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


