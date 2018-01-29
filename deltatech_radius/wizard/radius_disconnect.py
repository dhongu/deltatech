# coding=utf-8


from odoo import api, fields, models, tools, registry



class RediusDisconnect(models.TransientModel):
    _name = 'radius.disconnect'
    _description = 'Redius Disconnect'

    user_ids =  fields.Many2many("radius.radcheck")
    operation = fields.Selection([('d','disconnect'),('r','reconnect')], default='d')

    @api.model
    def default_get(self, fields):
        defaults = super(RediusDisconnect, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        user_ids  = self.env["radius.radcheck"]

        if active_model == 'account.move.line':
            partners = self.env['res.partner']
            move_lines = self.env[active_model].browse(active_ids)
            for move in move_lines:
                partners |= move.partner_id

            user_ids = self.env["radius.radcheck"].search([('partner_id','in',partners.ids)])

        if active_model == 'account.invoice':
            partners = self.env['res.partner']
            invoices = self.env[active_model].browse(active_ids)
            for invoice in invoices:
                partners |= invoice.partner_id

            user_ids = self.env["radius.radcheck"].search([('partner_id','in',partners.ids)])


        if active_model == 'radius.radcheck':
            user_ids = self.env[active_model].browse(active_ids)

        defaults['user_ids'] = [(6, 0, [rec.id for rec in user_ids])]
        return defaults

    @api.multi
    def do_disconnect(self):
        for user in self.user_ids:
            if self.operation == 'd':
                if user.radusergroup_id.groupname != 'disconected':
                    user.write({'groupname':user.radusergroup_id.groupname})
                    user.radusergroup_id.write({'groupname':'disconected'})
            else:
                if user.radusergroup_id.groupname == 'disconected' and user.groupname:
                    user.radusergroup_id.write({'groupname': user.groupname})

