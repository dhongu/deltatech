# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


# ca in SAP Material Valuation - MBEW & MBEWH
class ProductValuation(models.Model):
    _name = "product.valuation"
    _description = "Product Valuation"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product", required=True, index=True)
    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area", index=True)

    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", required=True, default=1.0)
    amount = fields.Monetary(string="Amount")

    account_id = fields.Many2one("account.account", string="Account", required=True, index=True)

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, index=True, default=lambda self: self.env.company
    )

    def get_valuation(self, product_id, valuation_area_id, account_id, company_id=False):
        if not company_id:
            company_id = self.env.company.id
        domain = [
            ("product_id", "=", product_id),
            ("valuation_area_id", "=", valuation_area_id),
            ("account_id", "=", account_id),
            ("company_id", "=", company_id),
        ]
        valuation = self.search(domain, limit=1)
        if not valuation:
            valuation = self.create(
                {
                    "product_id": product_id,
                    "valuation_area_id": valuation_area_id,
                    "account_id": account_id,
                    "company_id": company_id,
                }
            )
        return valuation

    def recompute_amount(self):
        valuation_areas = self.mapped("valuation_area_id")
        products = self.mapped("product_id")
        accounts = self.mapped("account_id")
        companies = self.mapped("company_id")
        domain = [
            ("product_id", "in", products.ids),
            ("account_id", "in", accounts.ids),
            ("company_id", "in", companies.ids),
        ]
        if valuation_areas:
            domain.append(("valuation_area_id", "in", valuation_areas.ids))

        params = {
            "product_ids": tuple(products.ids),
            "account_ids": tuple(accounts.ids),
            "company_ids": tuple(companies.ids),
            "valuation_area_ids": tuple(valuation_areas.ids) or (None,),
        }
        self.env.cr.execute(
            """
            SELECT product_id, valuation_area_id, account_id, m.company_id, move_type,
                sum(l.debit) as debit, sum(l.credit) as credit, sum(
                    l.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) * (
                    CASE WHEN m.move_type IN ('out_invoice','in_refund') THEN -1 ELSE 1 END
                    )
                ) as quantity
                FROM account_move_line as l
                LEFT JOIN account_move as m ON l.move_id=m.id
                LEFT JOIN product_product product ON product.id = l.product_id
                LEFT JOIN product_template template ON template.id = product.product_tmpl_id
                LEFT JOIN uom_uom uom_line ON uom_line.id = l.product_uom_id
                LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
                WHERE product_id in %(product_ids)s
                    AND account_id in %(account_ids)s
                    AND m.company_id in %(company_ids)s
                    AND (valuation_area_id in %(valuation_area_ids)s or valuation_area_id is null)
                    AND m.state = 'posted'
                GROUP BY  product_id, valuation_area_id, account_id, m.company_id, move_type
           """,
            params,
        )

        res = self.env.cr.dictfetchall()

        for valuation in self:
            valuation.amount = 0
            valuation.quantity = 0
            for line in res:
                if not line["valuation_area_id"]:
                    line["valuation_area_id"] = False
                if (
                    line["product_id"] == valuation.product_id.id
                    and line["valuation_area_id"] == valuation.valuation_area_id.id
                    and line["account_id"] == valuation.account_id.id
                    and line["company_id"] == valuation.company_id.id
                ):
                    valuation.quantity += line["quantity"]
                    valuation.amount += line["debit"] - line["credit"]


class ProductValuationHistory(models.Model):
    _name = "product.valuation.history"
    _description = "Product Valuation History"
    _inherit = ["product.valuation"]

    year = fields.Integer(string="Year", required=True, index=True)
    month = fields.Integer(string="Month", required=True, index=True)

    def recompute_amount(self):
        valuation_areas = self.mapped("valuation_area_id")
        products = self.mapped("product_id")
        accounts = self.mapped("account_id")
        companies = self.mapped("company_id")
        domain = [
            ("valuation_area_id", "in", valuation_areas.ids),
            ("product_id", "in", products.ids),
            ("account_id", "in", accounts.ids),
            ("company_id", "in", companies.ids),
        ]
        # de citit dupa an si luna
        group_fields = ["product_id", "valuation_area_id", "account_id", "company_id", "date:year", "date:month"]
        read_fields = [
            "product_id",
            "valuation_area_id",
            "account_id",
            "company_id",
            "date",
            "quantity",
            "debit",
            "credit",
        ]

        move_lines = self.env["account.move.line"].read_group(domain, read_fields, group_fields)
        for valuation in self:
            valuation.amount = 0
            valuation.quantity = 0
            for line in move_lines:
                if (
                    line["product_id"][0] == valuation.product_id.id
                    and line["valuation_area_id"][0] == valuation.valuation_area_id.id
                    and line["account_id"][0] == valuation.account_id.id
                ):
                    valuation.quantity += line["quantity"]
                    valuation.amount += line["debit"] - line["credit"]


# todo: de facut evaluarea si la nivel de lot
