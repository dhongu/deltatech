# -*- coding: utf-8 -*-

import time
import copy
import io
import base64
import math
import md5
import re
import traceback
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from PIL import Image

try:
    import jcconv
except ImportError:
    jcconv = None

try: 
    import qrcode
except ImportError:
    qrcode = None

 
from exceptions import *

try: 
    import html2text
except:
    from openerp.addons.email_template import html2text

import os.path  

class Datecs:
    """ Datecs Printer object """
    device    = None
    encoding  = None
    img_cache = {}

 

    def receipt(self,xml):
        """
        Prints an xml based receipt definition
        """
#        try:
        #root            = ET.fromstring(xml.encode('utf-8'))
        print xml
        text = html2text.html2text(xml) #.decode('utf8','replace'))  
        text = text.replace(chr(13), '\n')
        text = text.replace('\n\n', '\r\n')
        
         # Create data file
         
        fname = "/fprint/for_print/in.inp"   
        while os.path.isfile(fname): 
            print "FPrint nu a terminat tiparirea fisierului"
        data = open(fname, "w")
        data.write(text)
        data.close()
        
        
        #for line in text:
        #    self.text(line)  #"S,1,______,_,__;TEST;3.50;1.000;1;2;1;0;0;")


#        except Exception as e:
#            raise e

    def text(self,txt):
        """ Print Utf8 encoded alpha-numeric text """
        if not txt:
            return
        try:
            txt = txt.decode('utf-8')
        except:
            try:
                txt = txt.decode('utf-16')
            except:
                pass

        self._raw(txt)
        
    def set(self, align='left', font='a', type='normal', width=1, height=1):
        """ Set text properties """
        pass


    def cut(self, mode=''):
        """ Cut paper """
        pass


    def cashdraw(self, pin):
        """ Send pulse to kick the cash drawer """
        pass


    def hw(self, hw):
        """ Hardware operations """
        pass


    def control(self, ctl):
        """ Feed control sequences """
        pass
