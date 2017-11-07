# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Widget Google Maps',
    'sequence': 10,
    'description': """
    
Ofera functionalitatea de  editare de locatii si trasee pe harta de la goolge

1. Locatie - permite afisarea si editarea unui marker pe harta google
    <widget type="gmap_marker" lat="field_lat" lng="field_lng" description="field_descriptions"/>
2. Locatii - permite afisarea unei liste de locatii pe harta de la google
     <widget type="gmap_markers" lat="field_lat" lng="field_lng" description="field_descriptions"/>
3. Route - permite afisarea rute pe harta google
    <widget type="gmap_route" from_lat="field_from_lat" from_lng="field_from_lng" 
                              to_lat="field_to_lat" to_lng="field_to_lng" />

    
    """,
    'version': '1.2',
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'category': 'Odoo  widgets',
    'depends': ['web'],
    'data': ['views/web_gmaps_assets.xml'  ],

    'qweb': [
        'static/src/xml/resource.xml'
    ],
    'installable': True,
    'application': False,
    'bootstrap': True,
    'auto_install': False,
}


