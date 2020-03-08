# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models,tools, fields, api, _
from odoo.api import Environment
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
import threading
import odoo


from pyrfc import Connection
from pyrfc import ABAPApplicationError, ABAPRuntimeError, LogonError, CommunicationError

import logging
_logger = logging.getLogger(__name__)

ICON_ERROR =    '<img src="/deltatech_connector_sap/static/src/img/s_s_ledr.gif">'
ICON_WARNING =  '<img src="/deltatech_connector_sap/static/src/img/s_s_ledy.gif">'
ICON_INFO =     '<img src="/deltatech_connector_sap/static/src/img/s_s_ledg.gif">'

class connector_sap(models.Model):
    _name = 'connector.sap'
    _description = "Connector SAP"
    _inherit = 'mail.thread'
 
    name  = fields.Char(string='Name')
    ashost = fields.Char(string='Host')
    sysnr =  fields.Char(string='System number', size=2)
    client = fields.Char(string='Client', size=3)
    lang  = fields.Char(string='Language', size=2)
    
    user = fields.Char(string='User')
    passwd = fields.Char(string='Password')
    
    werks = fields.Char(string='Plant', size=4,default='1000')

  
    def init_connection(self):
        #TODO: daca nu sunt salvate datele de user si parola trebuie sa fie afisata o fereasta prin care se cere userul si parola
        try:
            sap_conn = Connection(ashost=self.ashost, sysnr=self.sysnr, client=self.client, user=self.user, passwd=self.passwd, lang=self.lang)  

        except CommunicationError as e:
            raise Warning(_("Connection test failed! /n Could not connect to server."))
        except LogonError as e:
            raise Warning(_("Connection test failed! /n Could not log in. Wrong credentials?"))
        except Exception as e:
            raise Warning(_("Connection test failed! /n Here is what we got instead:\n %s.") % tools.ustr(e))
        
        self.message_post(body=ICON_INFO + _("Successful connection to SAP"))
        
        return sap_conn
    
    @api.one
    def button_confirm_login(self):      
        sap_conn = self.init_connection()
         
        sap_conn.close()
        return True
 
 
    @api.multi
    def button_load_material_master(self):
        
        sap_conn = self.init_connection()
        
        REQUTEXT={
                  'MATNRSELECTION': [{ 'MATNR_LOW': '*', 'MATNR_HIGH': '', 'OPTION': 'CP', 'SIGN': 'I'}],
                  'PLANTSELECTION': [{ 'PLANT_LOW': self.werks, 'PLANT_HIGH': '', 'OPTION': 'EQ', 'SIGN': 'I'}]}
        try:
            result = sap_conn.call('BAPI_MATERIAL_GETLIST', **REQUTEXT) 
        except Exception as e:
            raise Warning(_("Remote Function Call! /n Here is what we got instead:\n %s.") % tools.ustr(e))
        
        
 
        for msg in result['RETURN']:
            if msg['TYPE'] == 'E' or msg['TYPE'] == 'A' :
                self.message_post(body=ICON_ERROR + msg['MESSAGE'])
            elif msg['TYPE'] == 'W':
                self.message_post(body=ICON_WARNING + msg['MESSAGE'])
            else:
                self.message_post(body=ICON_INFO + msg['MESSAGE'])  
         

            
        args=(  result['MATNRLIST'], sap_conn )
        threaded_add_material = threading.Thread(target=self.add_materials_bg, args=args)
        threaded_add_material.start()
            
        return True

    
    def add_materials_bg(self, cr, uid, ids, materials, sap_conn, context):
        with Environment.manage():
            new_cr = self.pool.cursor()
            for material in materials:
                cod_material = material['MATERIAL'] #.lstrip("0")
                description =  material['MATL_DESC']
                self.add_material(new_cr, uid, ids,   cod_material, sap_conn, context)
                new_cr.commit()
            new_cr.close()
            return {}  
            
 
            
    @api.multi  
    def add_material(self,  cod_material, sap_conn=None ):            
        
        if sap_conn is None:
                sap_conn = self.init_connection() 
        
        domain = [('default_code','=', cod_material.lstrip("0"))]
        product_obj =  self.env['product.product']
        product = product_obj.search(domain)
        if not product:

            # materialul nu exista si trebuie adaugat
            
            REQUTEXT={'MATERIAL':cod_material}
            
            try:
                result = sap_conn.call('BAPI_MATERIAL_GET_DETAIL', **REQUTEXT)
            except Exception as e:
                raise Warning(_("Remote Function Call! /n Here is what we got instead:\n %s.") % tools.ustr(e))
            
            is_ok = True
            
            if result['RETURN']['TYPE'] == 'S':
                is_ok = True
            else:
                is_ok = False
                self.message_post(body=result['RETURN']['MESSAGE'])           
            
            if is_ok:
                material = result['MATERIAL_GENERAL_DATA']
                
                # in functie de material['MATL_TYPE'] sau de material['MATL_GROUP'] se va determina o categorie de material !!
                msg = _("New product %s description  %s") %  (cod_material.lstrip("0"),material['MATL_DESC'])
                print (msg)
                self.message_post(body= msg)
                values = {
                            'name':material['MATL_DESC'],
                            'default_code':cod_material.lstrip("0"),
                            'ean13':material['EAN_UPC'],
                            'volume':material['VOLUME'],
                            'weight':material['GROSS_WT'],
                            'weight_net':material['NET_WEIGHT'],
                        }
                uom =  self.env['product.uom'].search([('name','=ilike',material['BASE_UOM'])])
                if uom:
                    values['uom_id'] = uom.id
                    values['uom_po_id'] = uom.id
                try:
                    product_obj.create(values)
                    
                except Exception as e:
                     self.message_post(body=   _("Here is what we got instead:\n %s.") % tools.ustr(e) )
            
