# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models

# worker_module = 'res.partner'
worker_module = "hr.employee"


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    partial_record = fields.Boolean(string="Partial production", help="Partial record production", defalut=False)
    start_without_stock = fields.Boolean(string="Start without stock", defalut=True)
    record_real_time = fields.Boolean(string="Real Time", default=True)
    worker_ids = fields.One2many("mrp.workcenter.worker", "workcenter_id", string="Workers")
    # mutat  in mrp_cost
    # costs_hour = fields.Float(string='Cost per hour', help="Specify cost of work center per hour.")
    # costs_hour_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
    #                                         help="Fill this only if you want automatic analytic accounting entries on production orders.")


class MrpWorkcenterWorkers(models.Model):
    _name = "mrp.workcenter.worker"
    _description = "Work Center Worker"
    _order = "to_date DESC"

    workcenter_id = fields.Many2one("mrp.workcenter", string="Work Center", required=True)
    # worker_id = fields.Many2one('res.partner', string="Worker", domain=[('is_company','=',False)])
    worker_id = fields.Many2one(worker_module, string="Worker")
    from_date = fields.Date(string="Form Date", default=lambda *a: fields.Date.today())
    to_date = fields.Date(string="To Date", default="2099-12-31")

    # todo: de verificat daca un muncitor se gaseste  in doua inregistrari care au intervalele suprapuse
