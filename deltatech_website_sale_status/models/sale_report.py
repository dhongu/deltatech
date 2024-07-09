# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    stage = fields.Selection(
        [
            ("placed", "Placed"),  # comanda plasta pe website
            ("in_process", "In Process"),  # comanda in procesare de catre agentul de vanzare
            ("waiting", "Waiting availability"),  # nu sunt in stoc toate produsele din comanda
            ("postponed", "Postponed"),  # livrarea a fost amanata
            ("to_be_delivery", "To Be Delivery"),  # comanda este de livrat
            ("in_delivery", "In Delivery"),  # marfa a fost predata la curier
            ("delivered", "Delivered"),  # comanda a fost livrata la client
            ("canceled", "Canceled"),
            ("returned", "Returned"),
        ],
        string="Stage",
        index=True,
    )

    def _select_additional_fields(self):
        additional_fields_info = super()._select_additional_fields()
        additional_fields_info[
            "stage"
        ] = """
            stage
        """
        return additional_fields_info

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += " ,stage "
        return res