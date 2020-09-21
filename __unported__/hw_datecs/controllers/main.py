# -*- coding: utf-8 -*-
import commands
import logging
import simplejson
import os
import os.path
import io
import base64
import odoo
import time
import random
import math
import md5
import odoo.addons.hw_proxy.controllers.main as hw_proxy
import pickle
import re
import subprocess
import traceback


from .. datecs import *
from .. datecs.exceptions import *
from .. datecs.printer import Usb

#    datecs = printer = None

from threading import Thread, Lock
from Queue import Queue, Empty

try:
    import usb.core
except ImportError:
    usb = None

from PIL import Image

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

# workaround https://bugs.launchpad.net/openobject-server/+bug/947231
# related to http://bugs.python.org/issue7980
from datetime import datetime
datetime.strptime('2012-01-01', '%Y-%m-%d')

class DatecsDriver(Thread):
    def __init__(self):
        _logger.info("Datecs init")
        Thread.__init__(self)
        self.queue = Queue()
        self.lock  = Lock()
        self.status = {'status':'connecting', 'messages':[]}

    def connected_usb_devices(self):
        connected = []

        # printers can either define bDeviceClass=7, or they can define one of
        # their interfaces with bInterfaceClass=7. This class checks for both.
        class FindUsbClass(object):
            def __init__(self, usb_class):
                self._class = usb_class
            def __call__(self, device):
                # first, let's check the device
                if device.bDeviceClass == self._class:
                    return True
                # transverse all devices and look through their interfaces to
                # find a matching class
                for cfg in device:
                    intf = usb.util.find_descriptor(cfg, bInterfaceClass=self._class)

                    if intf is not None:
                        return True

                return False
         
        #printers = usb.core.find(find_all=True, custom_match=FindUsbClass(0))

        printers = []
        # 067b:2303 Prolific Technology, Inc. PL2303 Serial Port

        printers += usb.core.find(find_all=True, idVendor=0x067b, idProduct=0x2303)
        
        #0557:2008 ATEN International Co., Ltd UC-232A Serial Port [pl2303]
        
        printers += usb.core.find(find_all=True, idVendor=0x0557, idProduct=0x2008)
        

        
        for printer in printers:
             
            connected.append({
                'vendor': printer.idVendor,
                'product': printer.idProduct,
                'name': "Serial Port - Datecs",
            })
      
        
        
        return connected

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()
    
    def get_datecs_printer(self):
  
        printers = self.connected_usb_devices()
        if len(printers) > 0:
            self.set_status('connected','Connected to '+printers[0]['name'])
            return Usb(printers[0]['vendor'], printers[0]['product'])
        else:
            self.set_status('disconnected','Printer Not Found')
            return None

    def get_status(self):
        self.push_task('status')
        return self.status

    def open_cashbox(self,printer):
        printer.cashdraw(2)
        printer.cashdraw(5)

    def set_status(self, status, message = None):
        _logger.info(status+' : '+ (message or 'no message'))
        if status == self.status['status']:
            if message != None and (len(self.status['messages']) == 0 or message != self.status['messages'][-1]):
                self.status['messages'].append(message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

        if status == 'error' and message:
            _logger.error('Datecs Error: '+message)
        elif status == 'disconnected' and message:
            _logger.warning('Datecs Device Disconnected: '+message)

    def run(self):
        printer = None
        if not datecs:
            _logger.error('Datecs cannot initialize, please verify system dependencies.')
            return
        while True:
            try:
                error = True
                timestamp, task, data = self.queue.get(True)
                
                _logger.info('Datecs task (%s)', task)
                printer = self.get_datecs_printer()
                
                if printer == None:
                    if task != 'status':
                        self.queue.put((timestamp,task,data))
                    error = False
                    time.sleep(5)
                    continue
                elif task == 'receipt': 
                    if timestamp >= time.time() - 1 * 60 * 60:
                        self.print_receipt_body(printer,data)
                        printer.cut()
                elif task == 'xml_receipt':
                    if timestamp >= time.time() - 1 * 60 * 60:
                        printer.receipt(data)
                elif task == 'cashbox':
                    if timestamp >= time.time() - 12:
                        self.open_cashbox(printer)
                elif task == 'printstatus':
                    self.print_status(printer)
                elif task == 'status':
                    _logger.info('status')
                    pass
                error = False

            except NoDeviceError as e:
                print "No device found %s" %str(e)
            except HandleDeviceError as e:
                print "Impossible to handle the device due to previous error %s" % str(e)
            except TicketNotPrinted as e:
                print "The ticket does not seems to have been fully printed %s" % str(e)
            except NoStatusError as e:
                print "Impossible to get the status of the printer %s" % str(e)
            except Exception as e:
                self.set_status('error', str(e))
                errmsg = str(e) + '\n' + '-'*60+'\n' + traceback.format_exc() + '-'*60 + '\n'
                _logger.error(errmsg)
            finally:
                if error:
                    self.queue.put((timestamp, task, data))
                if printer:
                    printer.close()

    def push_task(self,task, data = None):
        self.lockedstart()
        self.queue.put((time.time(),task,data))

    def print_status(self,eprint):
        pass


    def print_receipt_body(self,eprint,receipt):

        def check(string):
            return string != True and bool(string) and string.strip()
        
        def price(amount):
            return ("{0:."+str(receipt['precision']['price'])+"f}").format(amount)
        
        def money(amount):
            return ("{0:."+str(receipt['precision']['money'])+"f}").format(amount)

        def quantity(amount):
            if math.floor(amount) != amount:
                return ("{0:."+str(receipt['precision']['quantity'])+"f}").format(amount)
            else:
                return str(amount)

        def printline(left, right='', width=40, ratio=0.5, indent=0):
            lwidth = int(width * ratio) 
            rwidth = width - lwidth 
            lwidth = lwidth - indent
            
            left = left[:lwidth]
            if len(left) != lwidth:
                left = left + ' ' * (lwidth - len(left))

            right = right[-rwidth:]
            if len(right) != rwidth:
                right = ' ' * (rwidth - len(right)) + right

            return ' ' * indent + left + right + '\n'
        
        def print_taxes():
            taxes = receipt['tax_details']
            for tax in taxes:
                eprint.text(printline(tax['tax']['name'],price(tax['amount']), width=40,ratio=0.6))

        # Receipt Header
        if receipt['company']['logo']:
            eprint.set(align='center')
            eprint.print_base64_image(receipt['company']['logo'])
            eprint.text('\n')
        else:
            eprint.set(align='center',type='b',height=2,width=2)
            eprint.text(receipt['company']['name'] + '\n')

        eprint.set(align='center',type='b')
        if check(receipt['company']['contact_address']):
            eprint.text(receipt['company']['contact_address'] + '\n')
        if check(receipt['company']['phone']):
            eprint.text('Tel:' + receipt['company']['phone'] + '\n')
        if check(receipt['company']['vat']):
            eprint.text('VAT:' + receipt['company']['vat'] + '\n')
        if check(receipt['company']['email']):
            eprint.text(receipt['company']['email'] + '\n')
        if check(receipt['company']['website']):
            eprint.text(receipt['company']['website'] + '\n')
        if check(receipt['header']):
            eprint.text(receipt['header']+'\n')
        if check(receipt['cashier']):
            eprint.text('-'*32+'\n')
            eprint.text('Served by '+receipt['cashier']+'\n')

        # Orderlines
        eprint.text('\n\n')
        eprint.set(align='center')
        for line in receipt['orderlines']:
            pricestr = price(line['price_display'])
            if line['discount'] == 0 and line['unit_name'] == 'Unit(s)' and line['quantity'] == 1:
                eprint.text(printline(line['product_name'],pricestr,ratio=0.6))
            else:
                eprint.text(printline(line['product_name'],ratio=0.6))
                if line['discount'] != 0:
                    eprint.text(printline('Discount: '+str(line['discount'])+'%', ratio=0.6, indent=2))
                if line['unit_name'] == 'Unit(s)':
                    eprint.text( printline( quantity(line['quantity']) + ' x ' + price(line['price']), pricestr, ratio=0.6, indent=2))
                else:
                    eprint.text( printline( quantity(line['quantity']) + line['unit_name'] + ' x ' + price(line['price']), pricestr, ratio=0.6, indent=2))

        # Subtotal if the taxes are not included
        taxincluded = True
        if money(receipt['subtotal']) != money(receipt['total_with_tax']):
            eprint.text(printline('','-------'));
            eprint.text(printline(_('Subtotal'),money(receipt['subtotal']),width=40, ratio=0.6))
            print_taxes()
            #eprint.text(printline(_('Taxes'),money(receipt['total_tax']),width=40, ratio=0.6))
            taxincluded = False


        # Total
        eprint.text(printline('','-------'));
        eprint.set(align='center',height=2)
        eprint.text(printline(_('         TOTAL'),money(receipt['total_with_tax']),width=40, ratio=0.6))
        eprint.text('\n\n');
        
        # Paymentlines
        eprint.set(align='center')
        for line in receipt['paymentlines']:
            eprint.text(printline(line['journal'], money(line['amount']), ratio=0.6))

        eprint.text('\n');
        eprint.set(align='center',height=2)
        eprint.text(printline(_('        CHANGE'),money(receipt['change']),width=40, ratio=0.6))
        eprint.set(align='center')
        eprint.text('\n');

        # Extra Payment info
        if receipt['total_discount'] != 0:
            eprint.text(printline(_('Discounts'),money(receipt['total_discount']),width=40, ratio=0.6))
        if taxincluded:
            print_taxes()
            #eprint.text(printline(_('Taxes'),money(receipt['total_tax']),width=40, ratio=0.6))

        # Footer
        if check(receipt['footer']):
            eprint.text('\n'+receipt['footer']+'\n\n')
        eprint.text(receipt['name']+'\n')
        eprint.text(      str(receipt['date']['date']).zfill(2)
                    +'/'+ str(receipt['date']['month']+1).zfill(2)
                    +'/'+ str(receipt['date']['year']).zfill(4)
                    +' '+ str(receipt['date']['hour']).zfill(2)
                    +':'+ str(receipt['date']['minute']).zfill(2) )


driver = DatecsDriver()

driver.push_task('printstatus')

hw_proxy.drivers['escpos'] = driver

class datecsProxy(hw_proxy.Proxy):
    

    @http.route('/hw_proxy/print_receipt', type='json', auth='none', cors='*')
    def print_receipt(self, receipt):
        _logger.info('Datecs: PRINT RECEIPT') 
        driver.push_task('receipt',receipt)

    @http.route('/hw_proxy/print_xml_receipt', type='json', auth='none', cors='*')
    def print_xml_receipt(self, receipt):
        _logger.info('Datecs: PRINT XML RECEIPT') 
        driver.push_task('xml_receipt',receipt)

