# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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
    "name" : "Deltatech Project  Extension",
    "version" : "1.10",
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    
    'category': 'Project Management',
    
    "depends" : ['deltatech',"project"],


    "description": """
Features:    
 
 
""",
    "data" : [
        'views/report_project_do_today.xml',
        'wizard/print_report_date_view.xml',
        "views/project_view.xml",
        "data/project_data.xml",
        'wizard/recurrence_view.xml',
        'wizard/task_set_progress_view.xml', 
        'views/res_config_view.xml'

    ],
    "active": False,
    "installable": True,
   
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
