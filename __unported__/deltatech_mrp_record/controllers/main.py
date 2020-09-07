# -*- coding: utf-8 -*

from odoo.addons.bus.controllers.main import BusController
from odoo.http import request


class MrpRecordController(BusController):

    def _poll(self, dbname, channels, last, options):

        if options.get('mrp.record'):
            channels = list(channels)
            mrp_record_channel = (request.db, 'mrp.record', options.get('mrp.record'))
            channels.append(mrp_record_channel)
        return super(MrpRecordController, self)._poll(dbname, channels, last, options)
