# coding=utf-8
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import Warning


# ----------------------------------------------------------
# Groups
# ----------------------------------------------------------
class radius_groups(models.Model):
    _name = "radius.groups"
    _description = "Groups"

    name = fields.Char('Name', size=64, index=1)


# ----------------------------------------------------------
# NAS
# ----------------------------------------------------------
class radius_nas(models.Model):
    _name = "radius.nas"
    _description = "Nas"
    _rec_name = 'nasname'


    nasname = fields.Char('Nas IP/Host', size=128, index=1)
    shortname = fields.Char('Nas Shortname', size=32)

    type = fields.Selection([('cisco', 'cisco'), ('portslave', 'portslave'), ('other', 'other')], 'Nas Type',
                            size=32, default='other')
    ports = fields.Integer('Nas Ports')
    secret = fields.Char('Nas Secret', size=64)
    server = fields.Char('Nas Secret', size=64)
    community = fields.Char('Nas Community', size=64)
    description = fields.Text('Nas Description')


# ----------------------------------------------------------
# Radacct
# ----------------------------------------------------------
class radius_radacct(models.Model):
    _name = "radius.radacct"
    _description = "Radacct"

    name = fields.Char('Name', size=64) # new
    radacctid = fields.Integer(related='id', string='Rad Acct Id')  #care trbuie sa fie de fapt ID
    acctsessionid = fields.Char('Acct Session id', size=64)
    acctuniqueid = fields.Char('Acct Unique id', size=64)
    username = fields.Char('User Name', size=128)
    groupname = fields.Char('Group Name', size=128)
    realm = fields.Char('Realm', size=64)
    nasipaddress = fields.Char('Nas IP Address', size=64)
    nasportid = fields.Char('Nas Port Id', size=64)
    nasporttype = fields.Char('Nas port type', size=64)
    acctstarttime = fields.Datetime('Acct Start time')
    acctupdatetime  = fields.Datetime('Acct Update time')
    acctstoptime = fields.Datetime('Acct stop time')
    acctinterval = fields.Integer(string="Acct Interval")
    acctsessiontime = fields.Integer('Acct session time')
    acctauthentic = fields.Char('Acct authentic', size=32)
    connectinfo_start = fields.Char('Connect info start', size=64)
    connectinfo_stop = fields.Char('Connect info stop', size=64)
    acctinputoctets = fields.Float('Acct input octets')
    acctoutputoctets = fields.Float('Acct output octets')
    calledstationid = fields.Char('Called station id', size=64)
    callingstationid = fields.Char('Calling station id', size=64)
    acctterminatecause = fields.Char('Acct terminate cause', size=32)
    servicetype = fields.Char('Service Type', size=32)

    xascendsessionsvrkey = fields.Char('Xascendsessionsvrkey', size=32)  #new
    framedprotocol = fields.Char('Framed Protocol', size=32)
    framedipaddress = fields.Char('Framed IP Address', size=128)

    acctstartdelay = fields.Integer('Acct start delay') #new
    acctstopdelay = fields.Integer('Acct stop delay')   #new


# ----------------------------------------------------------
# Radcheck
# ----------------------------------------------------------
class radius_radcheck(models.Model):
    _name = "radius.radcheck"
    _description = "Radcheck"
    _rec_name = 'username'

    username = fields.Char('Username', size=64, index=1)
    #        'attribute': fields.char('Attribute', size=64)
    attribute = fields.Selection([('Cleartext-Password', 'Cleartext-Password'), ('Auth-Type', 'Auth-Type'),
                                  ('ChilliSpot-Max-Total-Octets', 'Quota Attribute'),
                                  ('ChilliSpot-Max-Total-Gigawords', 'Quota Gigawords'),
                                  ('Simultaneous-Use', 'Simultaneous-Use')], 'Attribute',
                                 default='Cleartext-Password', size=64)
    op = fields.Selection(
        [('=', '='), (':=', ':='), ('==', '=='), ('+=', '+='), ('!=', '!='), ('>', '>'), ('>=', '>='),
         ('<', '<'), ('<=', '<='), ('=~', '=~')], 'OP')
    value = fields.Char('Value', size=253)

    partner_id = fields.Many2one('res.partner',compute='_compute_partner', string='Customer', store = True)


    @api.depends('username')
    def _compute_partner(self):
        for rec in self:
            uname = rec.username.replace('A','').replace('B','').replace('C','')
            partner = self.env['res.partner'].search([('ref','=',uname)], limit=1)
            if partner:
                rec.partner_id  = partner

# ----------------------------------------------------------
# Radreply
# ----------------------------------------------------------
class radius_radreply(models.Model):
    _name = "radius.radreply"
    _description = "Radreply"

    username = fields.Char('Username', size=64, index=1)
    #        'attribute': fields.char('Attribute', size=64)
    attribute = fields.Selection([('Reply-Message', 'Reply-Message'), ('Idle-Timeout', 'Idle-Timeout'),
                                  ('Session-Timeout', 'Session-Timeout'),
                                  ('WISPr-Redirection-URL', 'WISPr-Redirection-URL'),
                                  ('WISPr-Bandwidth-Max-Up', 'WISPr-Bandwidth-Max-Up'),
                                  ('WISPr-Bandwidth-Max-Down', 'WISPr-Bandwidth-Max-Down')], 'Attribute',
                                 size=64)
    op = fields.Selection(
        [('=', '='), (':=', ':='), ('==', '=='), ('+=', '+='), ('!=', '!='), ('>', '>'), ('>=', '>='),
         ('<', '<'), ('<=', '<='), ('=~', '=~')], 'OP')
    value = fields.Char('Value', size=253)


# ----------------------------------------------------------
# Radgroupcheck
# ----------------------------------------------------------
class radius_radgroupcheck(models.Model):
    _name = "radius.radgroupcheck"
    _description = "Radgroupcheck"


    def _get_groupname(self):
        list = []
        groupname = self.env['radius.groups'].search([])
        for item in groupname:
            list += [(item.name,item.name)]
        return list


    groupname = fields.Selection(_get_groupname, string='Group Name')
    #        'attribute': fields.char('Attribute', size=64),
    attribute = fields.Selection([('Auth-Type', 'Auth-Type'), ('Max-All-Session', 'Max-All-Session'),
                                  ('Max-Monthly-Session', 'Max-Monthly-Session'),
                                  ('Pool-Name','Pool-Name'),
                                  ('Simultaneous-Use', 'Simultaneous-Use')], 'Attribute', size=64)
    op = fields.Selection(
        [('=', '='), (':=', ':='), ('==', '=='), ('+=', '+='), ('!=', '!='), ('>', '>'), ('>=', '>='),
         ('<', '<'), ('<=', '<='), ('=~', '=~')], 'OP')
    value = fields.Char('Value', size=253)


# ----------------------------------------------------------
# Radgroupreply
# ----------------------------------------------------------
class radius_radgroupreply(models.Model):
    _name = "radius.radgroupreply"
    _description = "Radgroupreply"

    def _get_groupname(self):
        list = []
        groupname = self.env['radius.groups'].search([])
        for item in groupname:
            list += [(item.name,item.name)]
        return list


    groupname = fields.Selection(_get_groupname, string='Group Name')
    #        'attribute': fields.char('Attribute', size=64),


    attribute = fields.Selection([
        ('Framed-Compression','Framed-Compression'),
        ('Framed-Protocol','Framed-Protocol'),
        ('Service-Type','Service-Type'),
        ('Mikrotik-Rate-Limit','Mikrotik-Rate-Limit'),
        ('MS-Primary-DNS-Server','MS-Primary-DNS-Server'),
        ('MS-Secondary-DNS-Server','MS-Secondary-DNS-Server'),
        ('Reply-Message', 'Reply-Message'),
                                  ('Idle-Timeout', 'Idle-Timeout'),
                                  ('Session-Timeout', 'Session-Timeout'),
                                  ('WISPr-Redirection-URL', 'WISPr-Redirection-URL'),
                                  ('WISPr-Bandwidth-Max-Up', 'WISPr-Bandwidth-Max-Up'),
                                  ('WISPr-Bandwidth-Max-Down', 'WISPr-Bandwidth-Max-Down')], 'Attribute',
                                 size=64)
    op = fields.Selection(
        [('=', '='), (':=', ':='), ('==', '=='), ('+=', '+='), ('!=', '!='), ('>', '>'), ('>=', '>='),
         ('<', '<'), ('<=', '<='), ('=~', '=~')], 'OP')
    value = fields.Char('Value', size=253)


radius_radgroupreply()


# ----------------------------------------------------------
# Radusergroup
# ----------------------------------------------------------
class radius_radusergroup(models.Model):
    _name = "radius.radusergroup"
    _description = "Radusergroup"
    _rec_name = 'username'


    def _get_groupname(self):
        list = []
        groupname = self.env['radius.groups'].search([])
        for item in groupname:
            list += [(item.name,item.name)]
        return list


    groupname = fields.Selection(_get_groupname, string='Group Name')
    username = fields.Char('Username', size=64, index=1)
    priority = fields.Integer('priority')


    partner_id = fields.Many2one('res.partner', compute='_compute_partner', string='Customer')


    @api.depends('username')
    def _compute_partner(self):
        for rec in self:
            uname = rec.username.replace('A', '').replace('B', '').replace('C', '')
            partner = self.env['res.partner'].search([('ref', '=', uname)], limit=1)
            if partner:
                rec.partner_id = partner


# ----------------------------------------------------------
# Radpostauth
# ----------------------------------------------------------
class radius_radpostauth(models.Model):
    _name = "radius.radpostauth"
    _description = "radpostauth"

    _fields = {
        'pass' : fields.Char(  string='Password', size=64)
    }

    username = fields.Char('Username', size=128, index=1)
    password  = fields.Char(name='pass', string='Password', size=64)
    reply = fields.Char('Radius Reply', size=64)
    calledstationid = fields.Char('Called station id', size=64)
    callingstationid = fields.Char('Calling station id', size=64)
    authdate = fields.Datetime('Auth Date')

