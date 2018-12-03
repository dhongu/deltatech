# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class service_agreement(models.Model):
    _inherit = 'service.agreement'

    @api.multi
    def service_equipment(self):
        equipments = self.env['service.equipment']

        for item in self.agreement_line:
            if item.equipment_id:
                equipments = equipments + item.equipment_id

        res = []
        for equipment in equipments:
            res.append(equipment.id)

        return {
            'domain': "[('id','in', [" + ','.join(map(str, res)) + "])]",
            'name': _('Services Equipment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.equipment',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }


class service_agreement_line(models.Model):
    _inherit = 'service.agreement.line'

    equipment_id = fields.Many2one('service.equipment', string='Equipment', index=True)
    meter_id = fields.Many2one('service.meter', string='Meter')

    # de adaugat constringerea ca unitatea de masura de la linie sa fi la fel ca si cea de la meter

    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.meter_id = self.equipment_id.meter_ids[0]

    @api.onchange('meter_id')
    def onchange_meter_id(self):
        if self.meter_id:
            self.equipment_id = self.meter_id.equipment_id
            # self.uom_id = self.meter_id.uom_id

    @api.model
    def old_after_create_consumption(self, consumption, backup_equipment=False):
        # readings = self.env['service.meter.reading']
        # la data citirii echipamentul functiona in baza contractului???\\
        # daca echipamentul a fost inlocuit de unul de rezeva ?

        self.ensure_one()
        res = [consumption.id]  # trebuie musai fa folosesc super ???
        if self.equipment_id:

            # echipamentul are instalari dezintalari in perioada  ?
            if self.meter_id and backup_equipment:
                meter = backup_equipment.meter_ids.filtered(lambda r: r.uom_id.id == self.meter_id.uom_id.id)
            else:
                meter = self.meter_id

            if backup_equipment:
                equipment = backup_equipment
            else:
                equipment = self.equipment_id

            de_la_data = self.equipment_history_id.from_date
            readings = meter.meter_reading_ids.filtered(lambda r: r.consumption_id)
            if readings:
                de_la_data = max([readings[0].date, de_la_data])

            if meter:
                # se selecteaza citirile care nu sunt facturate
                # se selecteaza citirile care sunt anterioare sfarsitului de perioada, e pozibil ca sa mai fie citiri in perioada anterioara nefacturate

                readings = meter.meter_reading_ids.filtered(lambda r: not r.consumption_id and
                                                                      r.date <= consumption.period_id.date_stop and
                                                                      r.date >= de_la_data)  # sa fie dupa data de instalare si dupa ultima citire facturata
                # se selecteaza citirile pentru intervalul in care echipamentul era instalat la client

                if readings:
                    end_date = max(readings[0].date, consumption.period_id.date_stop)
                    start_date = min(readings[-1].date, consumption.period_id.date_start)
                else:
                    end_date = consumption.period_id.date_start
                    start_date = consumption.period_id.date_stop

                # print start_date, end_date, readings
                # de ce mai determin citirile cand : pentru a scoate citirile care au facuta cand echipamentul era dezinstalat sau backup
                domain = [('id', 'in', readings.ids),
                          ('equipment_history_id.address_id', 'child_of', self.agreement_id.partner_id.id)]

                readings = self.env['service.meter.reading'].search(domain)
                quantity = 0
                # print start_date, end_date, readings
                for reading in readings:
                    from_uom = reading.meter_id.uom_id
                    to_uom = consumption.agreement_line_id.uom_id

                    amount = reading.difference / from_uom.factor
                    if to_uom:
                        amount = amount * to_uom.factor

                    quantity += amount

                name = self.equipment_id.display_name + '\n'
                if backup_equipment:
                    name += _('Backup') + backup_equipment.display_name + '\n'
                if readings:
                    first_reading = readings[-1]
                    last_reading = readings[0]
                    name += _('Old index: %s, New index:%s') % (
                    first_reading.previous_counter_value, last_reading.counter_value)
                    if self.invoice_description != '' and self.invoice_description != False:
                        name = self.invoice_description
                    readings.write({'consumption_id': consumption.id})
                if self.invoice_description != '' and self.invoice_description != False:
                    name = self.invoice_description
                if quantity != 0 or consumption.agreement_line_id.active:
                    consumption.write({'quantity': quantity,
                                       'name': name,
                                       'equipment_id': equipment.id,
                                       'address_id': equipment.address_id.id
                                       })

                # determin daca in interval echipamentul a fost inlcuit de altul
                domain = [('equipment_id', '=', equipment.id), ('from_date', '>=', start_date),
                          ('from_date', '<=', end_date)]

                equipment_hist_ids = self.env['service.equipment.history'].search(domain)
                equipments = self.env['service.equipment']
                for equi_hist in equipment_hist_ids:
                    equipments |= equi_hist.equipment_backup_id
                for equi in equipments:
                    cons_value = self.get_value_for_consumption()
                    if cons_value:
                        cons_value.update({
                            'partner_id': consumption.partner_id.id,
                            'period_id': consumption.period_id.id,
                            'agreement_id': consumption.agreement_id.id,
                            'agreement_line_id': consumption.agreement_line_id.id,
                            'date_invoice': consumption.date_invoice,
                            'address_id': consumption.address_id,
                        })
                        new_consumption = self.env['service.consumption'].create(cons_value)

                        res = res.extend(self.after_create_consumption(new_consumption, equi))

            else:  # echipament fara contor
                cons_value = {'name': self.invoice_description or self.equipment_id.display_name,
                              'equipment_id': equipment.id, 'address_id': equipment.address_id.id}
                if not consumption.agreement_line_id.active:
                    # cons_value['quantity'] = 0
                    consumption.unlink()
                else:
                    consumption.write(cons_value)

        else:
            if self.invoice_description != '':
                consumption.write({'name': self.invoice_description})
                res = [consumption.id]
        return res

    @api.model
    def after_create_consumption(self, consumption):
        # readings = self.env['service.meter.reading']
        # la data citirii echipamentul functiona in baza contractului???\\
        # daca echipamentul a fost inlocuit de unul de rezeva ?

        self.ensure_one()
        res = [consumption.id]  # trebuie musai fa folosesc super ???
        if self.equipment_id:

            meter = self.meter_id
            equipment = self.equipment_id
            de_la_data = consumption.agreement_id.date_agreement  # si eventual de pus data de instalare
            if meter:




                # se citesc inregistrarile la care a fost generat cosnumul
                readings = meter.meter_reading_ids.filtered(lambda r: r.consumption_id)
                if readings:
                    de_la_data = max([readings[0].date, de_la_data])

                # se selecteaza citirile care nu sunt facturate
                # se selecteaza citirile care sunt anterioare sfarsitului de perioada, e pozibil ca sa mai fie citiri in perioada anterioara nefacturate

                readings = meter.meter_reading_ids.filtered(lambda r: not r.consumption_id and
                                                                      r.date <= consumption.period_id.date_end and
                                                                      r.date >= de_la_data)  # sa fie dupa data de instalare si dupa ultima citire facturata



                if readings:
                    end_date = max(readings[0].date, consumption.period_id.date_end)
                    start_date = min(readings[-1].date, consumption.period_id.date_start)
                else:
                    end_date = consumption.period_id.date_start
                    start_date = consumption.period_id.date_end


                quantity = 0

                for reading in readings:
                    from_uom = reading.meter_id.uom_id
                    to_uom = consumption.agreement_line_id.uom_id

                    amount = reading.difference / from_uom.factor
                    if to_uom:
                        amount = amount * to_uom.factor

                    quantity += amount

                name = self.equipment_id.display_name + '\n'

                if readings:
                    first_reading = readings[-1]
                    last_reading = readings[0]
                    name += _('Old index: %s, New index:%s') % (first_reading.previous_counter_value, last_reading.counter_value)

                    readings.write({'consumption_id': consumption.id})

                consumption.write({
                    'quantity': quantity,
                    'name': name,
                    'equipment_id': equipment.id
                })


            else:  # echipament fara contor
                consumption.write({'name': self.equipment_id.display_name,
                                   'equipment_id': equipment.id})
        return res


class service_consumption(models.Model):
    _inherit = 'service.consumption'

    equipment_id = fields.Many2one('service.equipment', string='Equipment', index=True)

    _sql_constraints = [
        ('agreement_line_period_uniq', 'unique(period_id,agreement_line_id,equipment_id)',
         'Agreement line in period already exist!'),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
