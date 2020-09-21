# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError

# worker_module = 'res.partner'
worker_module = "hr.employee"


class MrpWorkRecord(models.TransientModel):
    _name = "mrp.work.record"
    _description = "MRP Record Production"
    _inherit = ["barcodes.barcode_events_mixin"]

    procurement_group_id = fields.Many2one("procurement.group", "Procurement Group")
    error_message = fields.Char(string="Error Message", readonly=True)
    success_message = fields.Char(string="Success Message", readonly=True)
    info_message = fields.Char(string="Info Message", readonly=True)

    @api.model
    def get_workers_ids(self, work_order_ids):
        productivity = self.env["mrp.workcenter.productivity"].search([("workorder_id", "in", work_order_ids)])
        productivity = productivity.filtered(lambda x: x.date_end is False)

        workers = self.env[worker_module]
        for prod in productivity:
            workers |= prod.worker_id

        return workers

    @api.model
    def get_workers_name(self, work_order_ids):
        workers = self.get_workers_ids(work_order_ids)
        return workers.read(["id", "name"])

    @api.model
    def search_scanned(self, barcode, values):
        action = self.on_barcode_scanned(barcode, values)
        if action["error_message"]:
            action.update(
                {"warning": {"title": "Warning", "message": action["error_message"]},}
            )

        return action

    @api.model
    def get_statistics(self, work_order_ids):
        values = self.env["mrp.workorder"].read_group(
            domain=[("id", "=", work_order_ids)],
            fields=["qty_production", "qty_produced", "duration_expected", "duration"],
        )
        return values

    @api.model
    def save_work(self, values):
        work_orders = self.env["mrp.workorder"].browse(values["work_order_ids"])
        for work_order in work_orders:
            work_order.record_production()
        values["work_order_ids"] = False
        values["info_message"] = _("Work orders was finished")
        return values

    @api.model
    def on_barcode_scanned(self, barcode, old_values=None):
        if not old_values:
            values = {}
        else:
            values = dict(old_values)

        values.update(
            {"error_message": False, "success_message": False, "info_message": False, "warning": False,}
        )

        if barcode == "#save":
            return self.save_work()

        nomenclature = self.env["barcode.nomenclature"].search([], limit=1)
        if not nomenclature:
            values["error_message"] = _("Barcode nomenclature not found")
            return values

        scann = nomenclature.parse_barcode(barcode)

        values["scann"] = scann

        if scann["type"] == "error":
            values["error_message"] = _("Invalid bar code %s") % barcode

        elif scann["type"] == "mrp_operation":
            workorder_domain = [("code", "=", barcode), ("state", "in", ["ready", "progress"])]
            if values.get("work_order_ids", False):
                workorder_domain += [("id", "in", values["work_order_ids"])]

            work_orders = self.env["mrp.workorder"].search(workorder_domain)
            if not work_orders:
                values["error_message"] = _("For the operation code %s there are no work order") % barcode
                values["operation_code"] = False
                values["work_order_ids"] = False
            else:
                values["info_message"] = _("Operation %s was scanned") % barcode
                values["work_order_ids"] = work_orders.ids
                values["work_order_limit_ids"] = work_orders.ids[:10]
                values["operation_code"] = barcode

        if "operation_code" not in values:
            values["error_message"] = _("Please scan first the operation")
            return values

        if scann["type"] == "mrp_operation":
            pass
        elif scann["type"] == "mrp_worker":
            domain = []
            if worker_module == "res.partner":
                domain = [("ref", "=", scann["code"])]
            if worker_module == "hr.employee":
                domain = [("barcode", "=", scann["code"])]

            worker = self.env[worker_module].search(domain, limit=1)
            if not worker:
                values["error_message"] = _("Worker %s not found") % barcode
            else:
                values["info_message"] = _("Worker %s was scanned") % worker.name

                # se gaeste in comanda de lucru?
                if values.get("work_order_ids", False):
                    loss_id = self.env["mrp.workcenter.productivity.loss"].search(
                        [("loss_type", "=", "productive")], limit=1
                    )
                    time_ids = self.env["mrp.workcenter.productivity"].search(
                        [
                            ("workorder_id", "in", values["work_order_ids"]),
                            ("worker_id", "=", worker.id),
                            ("date_end", "=", False),
                        ]
                    )
                    if time_ids:
                        time_ids.write({"date_end": fields.Datetime.now()})
                    else:
                        # lucreaza pe o alta comanda ?
                        time_ids = self.env["mrp.workcenter.productivity"].search(
                            [("worker_id", "=", worker.id), ("date_end", "=", False)]
                        )
                        if time_ids:
                            time_ids.write({"date_end": fields.Datetime.now()})
                        work_orders = self.env["mrp.workorder"].browse(values["work_order_ids"])
                        for work_order in work_orders:
                            self.env["mrp.workcenter.productivity"].create(
                                {
                                    "workorder_id": work_order.id,
                                    "workcenter_id": work_order.workcenter_id.id,
                                    "worker_id": worker.id,
                                    "loss_id": loss_id.id,
                                    "date_start": fields.Datetime.now(),
                                }
                            )
                #  trimite mesaj de refresh
                (channel, message) = ((self._cr.dbname, "mrp.record", True), ("refresh", True))
                self.env["bus.bus"].sendone(channel, message)

        elif scann["type"] == "product":
            domain = ["|", ("default_code", "=", scann["code"]), ("barcode", "=", scann["code"])]
            product = self.env["product.product"].search(domain, limit=1)
            if not product:
                values["error_message"] = _("pProduct %s not found") % barcode
            else:
                workorder_domain = [
                    ("raw_product_id", "=", product.id),
                    ("code", "=", values["operation_code"]),
                    ("state", "in", ["ready", "progress"]),
                ]
                work_orders = self.env["mrp.workorder"].search(workorder_domain)
                if not work_orders:
                    workorder_domain = [
                        ("product_id", "=", product.id),
                        ("code", "=", values["operation_code"]),
                        ("state", "in", ["ready", "progress"]),
                    ]
                    work_orders = self.env["mrp.workorder"].search(workorder_domain)
                if not work_orders:
                    values["error_message"] = _("For the product %s there are no work order") % product.name
                    values["work_order_ids"] = False
                else:
                    values["work_order_ids"] = work_orders.ids
                    values["work_order_limit_ids"] = work_orders.ids[:10]

        elif scann["type"] == "mrp_group":
            domain = [("name", "=", scann["code"])]
            procurement_group = self.env["procurement.group"].search(domain, limit=1)
            if not procurement_group:
                values["error_message"] = _("Work order group %s not found") % barcode
            else:
                values["info_message"] = _("Work order group %s was scanned") % procurement_group.name
                values["procurement_group_id"] = procurement_group.id

                workorder_domain = [
                    ("procurement_group_id", "=", procurement_group.id),
                    ("code", "=", values["operation_code"]),
                    ("state", "in", ["ready", "progress"]),
                ]
                if values.get("operation_code", False):
                    workorder_domain += [("code", "=", values["operation_code"])]
                work_orders = self.env["mrp.workorder"].search(workorder_domain)
                if not work_orders:
                    values["error_message"] = _("For the group %s there are no work order") % barcode
                    values["work_order_ids"] = False
                else:
                    values["work_order_ids"] = work_orders.ids
                    values["work_order_limit_ids"] = work_orders.ids[:10]
        else:
            values["error_message"] = _("The type %s is not used in this screen") % (scann["type"])

        return values
