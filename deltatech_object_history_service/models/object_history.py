# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class ObjectHistory(models.Model):
    _inherit = "object.history"

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if (
            "res_model" in res
            and res["res_model"]
            and "res_id" in res
            and res["res_id"]
            and (res["res_model"] == "service.agreement" or res["res_model"] == "service.equipment")
        ):
            parent = self.env[res["res_model"]].browse(res["res_id"])
            res["object_name"] = parent.name
        return res
