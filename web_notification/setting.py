from openerp import models, fields, api, sql_db
import thread
from time import sleep


class Setting(models.TransientModel):
    _name = 'web.notification.setting'
    _description = 'Setting for Notification'
    _inherit = 'res.config.settings'

    title = fields.Char()
    message = fields.Text()
    mode = fields.Selection(selection=[('notify', "Notification"),
                                       ('warn', 'Warning')],
                            default="notify",
                            required=True)
    makecheck = fields.Selection(selection=[('none', "None"),
                                            ('simple',
                                             "Only a simple notification"),
                                            ('withdelay', "Notification after "
                                             "a delay in second"),
                                            ('cron', "Notification by cron")],
                                 string="Make a ckeck",
                                 default='none',
                                 required=True)
    delay = fields.Integer(default=0)
    dt = fields.Datetime(string='Date time')
    user = fields.Many2one('res.users', default=lambda self: self.env.user,
                           required=True)

    @api.multi
    def button_check_notification(self):
        r = self.read(['title', 'message', 'mode'])[0]
        del r['id']
        self.user.post_notification(**r)
        return True

    @api.multi
    def button_check_notification_delay(self):
        r = self.read(['title', 'message', 'mode', 'delay'])[0]
        del r['id']
        delay = r.pop('delay')
        uid = self.user.id
        context = self.env.context

        def thread_method(dbname):
            sleep(delay)
            cursor = sql_db.db_connect(dbname).cursor()
            with api.Environment.manage():
                env = api.Environment(cursor, uid, context)
                env.user.post_notification(**r)

            cursor.commit()
            cursor.close()
            return True

        thread.start_new_thread(thread_method, (self.env.cr.dbname,))
        return True

    @api.multi
    def button_check_notification_cron(self):
        r = self.read(['title', 'message', 'mode', 'dt'])[0]
        uid = self.user.id
        context = self.env.context
        vals = {
            'name': "Check notification",
            'user_id': uid,
            'priority': 100,
            'numbercall': 1,
            'doall': True,
            'model': 'res.users',
            'function': 'post_notification',
            'args': str((uid, r['title'], r['message'], r['mode'], context)),
        }
        if r['dt']:
            vals.update({
                'nextcall': r['dt'],
            })

        self.sudo().env['ir.cron'].create(vals)
