from openerp import models, fields, api


class IrNotification(models.Model):
    _name = 'ir.notification'
    _description = 'Odoo Notification'

    mode = fields.Selection(selection=[('notify', 'Notification'),
                                       ('warn', 'Warning')],
                            required=True,
                            default='notify')
    subject = fields.Char(required=True)
    body = fields.Html(required=True)
    user_ids = fields.Many2many(comodel_name='res.users',
                                relation='user_notified_rel',
                                column1='notify_id',
                                column2='user_id')

    @api.model
    def create(self, values):
        res = super(IrNotification, self).create(values)
        vals = res.read()[0]
        bus = res.env['bus.bus']
        for user in res.user_ids:
            message = vals.copy()
            message['sticky'] = user.notification_sticky
            bus.sendone('notify_res_user_%d' % user.id, message)

        return res
