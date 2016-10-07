#!/usr/bin/python

import usb.core
import usb.util
import serial
import socket

from datecs import *
from exceptions import *
from time import sleep

class Usb(Datecs):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, interface=0, in_ep=0x82, out_ep=0x01):
        """
        @param idVendor  : Vendor ID
        @param idProduct : Product ID
        @param interface : USB device interface
        @param in_ep     : Input end point
        @param out_ep    : Output end point
        """

        self.errorText = ""

        self.idVendor  = idVendor
        self.idProduct = idProduct
        self.interface = interface
        self.in_ep     = in_ep
        self.out_ep    = out_ep
        self.open()

    def open(self):
        """ Search device on USB tree and set is as datecs device """
        self.device = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct)
        if self.device is None:
            raise NoDeviceError()
        try:
            if self.device.is_kernel_driver_active(self.interface):
                self.device.detach_kernel_driver(self.interface) 
            self.device.set_configuration()
            usb.util.claim_interface(self.device, self.interface)
        except usb.core.USBError as e:
            raise HandleDeviceError(e)

    def close(self):
        i = 0
        while True:
            try:
                if not self.device.is_kernel_driver_active(self.interface):
                    usb.util.release_interface(self.device, self.interface)
                    self.device.attach_kernel_driver(self.interface)
                    usb.util.dispose_resources(self.device)
                else:
                    self.device = None
                    return True
            except usb.core.USBError as e:
                i += 1
                if i > 10:
                    return False
        
            sleep(0.1)

    def _raw(self, msg):
        """ Print any command sent in raw format """
        if len(msg) != self.device.write(self.out_ep, msg, self.interface):
            self.device.write(self.out_ep, self.errorText, self.interface)
            raise TicketNotPrinted()
    


    def __del__(self):
        """ Release USB interface """
        if self.device:
            self.close()
        self.device = None



class Serial(Datecs):
    """ Define Serial printer """

    def __init__(self, devfile="/dev/ttyS0", baudrate=9600, bytesize=8, timeout=1):
        """
        @param devfile  : Device file under dev filesystem
        @param baudrate : Baud rate for serial transmission
        @param bytesize : Serial buffer size
        @param timeout  : Read/Write timeout
        """
        self.devfile  = devfile
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.timeout  = timeout
        self.open()


    def open(self):
        """ Setup serial port and set is as datecs device """
        self.device = serial.Serial(port=self.devfile, baudrate=self.baudrate, bytesize=self.bytesize, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=self.timeout, dsrdtr=True)

        if self.device is not None:
            print "Serial printer enabled"
        else:
            print "Unable to open serial printer on: %s" % self.devfile


    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.device.write(msg)


    def __del__(self):
        """ Close Serial interface """
        if self.device is not None:
            self.device.close()



class Network(Datecs):
    """ Define Network printer """

    def __init__(self,host,port=9100):
        """
        @param host : Printer's hostname or IP address
        @param port : Port to write to
        """
        self.host = host
        self.port = port
        self.open()


    def open(self):
        """ Open TCP socket and set it as datecs device """
        self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device.connect((self.host, self.port))

        if self.device is None:
            print "Could not open socket for %s" % self.host


    def _raw(self, msg):
        self.device.send(msg)


    def __del__(self):
        """ Close TCP connection """
        self.device.close()

