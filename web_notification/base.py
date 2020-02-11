from openerp import models, fields, api, _
from openerp.addons.base.res.res_users import res_users


res_users.SELF_WRITEABLE_FIELDS.append('notification_sticky')
res_users.SELF_READABLE_FIELDS.append('notification_sticky')


class ResUsers(models.Model):
    _inherit = 'res.users'

    notification_sticky = fields.Boolean(
        string='Notification sticky',
        default=True)

    @api.multi
    def post_notification(self, title='', message='', mode='notify'):
        vals = {
            'subject': title,
            'body': message,
            'user_ids': [(4, x.id) for x in self],
            'mode': mode,
        }
        return self.env['ir.notification'].create(vals)


    @api.multi
    def notify_danger(self, message):
        vals = {
            'subject': _('Warning'),
            'body': message,
            'user_ids': [(4, x.id) for x in self],
            'mode': 'warn',
        }
        return self.env['ir.notification'].with_context(sticky=False).create(vals)


    @api.multi
    def notify_info(self, message):
        vals = {
            'subject': _('Info'),
            'body': message,
            'user_ids': [(4, x.id) for x in self],
            'mode': 'notify',
        }
        return self.env['ir.notification'].with_context(sticky=False).create(vals)