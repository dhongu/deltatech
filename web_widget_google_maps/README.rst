.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3


Widget Goolge Map
=================


Usage
-----

It offers the functionality of editing locations and routes on the goolge map
 1. Location - Allows you to display and edit a marker on the google map: *<widget name="gmap_marker" lat="field_lat" lng="field_lng" />*
 2. Route - Allows you to display routes on the google map: *<widget name="gmap_route" from_lat="field_from_lat" from_lng="field_from_lng" to_lat="field_to_lat" to_lng="field_to_lng"/>*
 3. Locations - Allows you to display a list of locations on the google map



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

Contributors
------------

* Dorin Hongu <dhongu@gmail.com>


Maintainer
----------

.. image:: https://terrabit.ro/wp-content/uploads/2016/03/terra-menu.png
   :alt: Terrabit
   :target: https://terrabit.ro

This module is maintained by the Terrabit.