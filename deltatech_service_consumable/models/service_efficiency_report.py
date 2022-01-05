# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ServiceEfficiencyReport(models.Model):
    _name = "service.efficiency.report"
    _inherit = "stock.picking.report"
    _description = "ServiceEfficiencyReport"

    equipment_id = fields.Many2one("service.equipment", string="Equipment", index=True)
    agreement_id = fields.Many2one("service.agreement", string="Contract Services")
    usage = fields.Float(string="Usage", digits="Product UoM", readonly=True, compute="_compute_usage", store=True)
    uom_usage = fields.Many2one("uom.uom", string="Unit of Measure Usage", help="Unit of Measure for Usage", index=True)
    shelf_life = fields.Float(string="Shelf Life", digits="Product UoM")

    def _select(self):
        select_str = (
            super(ServiceEfficiencyReport, self)._select()
            + """,
                  sp.equipment_id,
                  equi.agreement_id,
                  0 as usage,
                  sum(sm.product_qty)*avg(pt.shelf_life) as shelf_life,
                  pt.uom_shelf_life as uom_usage
                """
        )
        return select_str

    def _from(self):
        from_str = (
            super(ServiceEfficiencyReport, self)._from()
            + """

                       INNER JOIN service_equipment as equi ON  sp.equipment_id = equi.id
                    """
        )
        return from_str

    def _group_by(self):
        group_by_str = (
            super(ServiceEfficiencyReport, self)._group_by() + ", sp.equipment_id, equi.agreement_id, pt.uom_shelf_life"
        )
        return group_by_str

    def _compute_usage(self):
        self.usage = 0.0

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        res = super(ServiceEfficiencyReport, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

        if "usage" in fields:
            for line in res:
                begin_date = "2000-01-01"
                end_date = "2999-12-31"
                product_id = False
                uom_usage = False
                equipment_id = False
                domain = line.get("__domain", [])
                for cond in domain:
                    if cond[0] == "date":
                        if cond[1] == ">=" or cond[1] == ">":
                            begin_date = cond[2]
                        if cond[1] == "<" or cond[1] == "<=":
                            end_date = cond[2]
                    if cond[0] == "equipment_id":
                        equipment_id = cond[2]
                    if cond[0] == "product_id":
                        product_id = cond[2]
                    if cond[0] == "uom_usage":
                        uom_usage = cond[2]

                usage = self.get_usage(begin_date, end_date, equipment_id, uom_usage, product_id)

                line["usage"] = usage

        return res

    @api.model
    def get_usage(self, begin_date, end_date, equipment_id, uom_usage, product_id):

        usage = 0
        if not uom_usage and product_id:
            product = self.env["product.product"].browse(product_id)
            if product:
                uom_usage = product.uom_shelf_life.id

        if uom_usage and equipment_id:
            uom = self.env["uom.uom"].browse(uom_usage)
            meters = self.env["service.meter"].search(
                [("equipment_id", "=", equipment_id), ("uom_id.category_id", "=", uom.category_id.id)]
            )

            if meters:
                meter_find = meters[0]
            else:
                meter_find = False

            for meter in meters:
                if meter.uom_id == uom:
                    meter_find = meter

            if meter_find:
                usage = meter_find.get_counter_value(begin_date, end_date)
                from_uom = meter_find.uom_id
                to_uom = uom
                usage = usage / from_uom.factor
                usage = usage * to_uom.factor

        return usage
