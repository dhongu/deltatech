# -*- coding: utf-8 -*-
import pytz
from odoo import   fields

def local_to_utc(event_time):
    tz_name = "Europe/Bucharest"
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(fields.Datetime.from_string(event_time), is_dst=None)
    event_time = fields.Datetime.to_string( local_dt.astimezone(pytz.utc) )
    return event_time

def utc_to_local(event_time):
    tz_name = "Europe/Bucharest"
    tz = pytz.timezone(tz_name)
    event_time = fields.Datetime.from_string(event_time)
    event_time = pytz.UTC.localize(event_time).astimezone(tz).replace(tzinfo=None)

    event_time = fields.Date.to_string( event_time )
    return event_time

d1 = '2018-01-15 06:00:00'
print (d1, local_to_utc(d1))

d1 = '2018-06-15 06:00:00'
print (d1, local_to_utc(d1))

d1 = '2018-01-15 04:00:00'
print (d1, utc_to_local(d1))

d1 = '2018-06-15 03:00:00'
print (d1, utc_to_local(d1))


d1 = '2018-01-15 00:00:00'
print (d1, local_to_utc(d1))

d1 = '2018-06-15 00:00:00'
print (d1, local_to_utc(d1))

d1 = '2018-01-15 22:00:00'
print (d1, utc_to_local(d1))

d1 = '2018-06-15 21:00:00'
print (d1, utc_to_local(d1))


