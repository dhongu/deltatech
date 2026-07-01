# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import random
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = "product.category"

    sequence_id = fields.Many2one("ir.sequence", string="Code Sequence")
    generate_barcode = fields.Boolean()
    prefix_barcode = fields.Char(default="40", size=2)
    barcode_random = fields.Boolean(default=True)


def _conflicting_company(company_a, company_b):
    """Doua coduri intra in conflict daca apartin aceleiasi companii sau daca
    cel putin unul e partajat (company_id = False) — in PostgreSQL NULL != NULL,
    deci o constrangere SQL unique(default_code, active, company_id) NU prinde
    duplicatele cu company_id NULL. De aceea verificam in Python."""
    return not company_a or not company_b or company_a == company_b


def _check_unique_default_code(records, company_of):
    """Verifica unicitatea default_code pe un recordset, cu O SINGURA interogare
    (nu una per inregistrare), ca sa scaleze la import/scriere in lot pe baze mari.
    `company_of(rec)` intoarce compania inregistrarii."""
    to_check = records.filtered(lambda p: p.default_code and p.active)
    if not to_check:
        return
    codes = list({p.default_code for p in to_check})
    # Uniqueness is over (default_code, active, company_id): an active and an
    # archived product may share a code (see show_not_unique). Force active_test
    # so ambient active_test=False (e.g. during marketplace import) does not make
    # archived records collide with active ones.
    by_code = defaultdict(list)
    for rec in records.with_context(active_test=True).search([("default_code", "in", codes)]):
        by_code[rec.default_code].append(rec)
    for product in to_check:
        company = company_of(product)
        for other in by_code[product.default_code]:
            if other.id != product.id and _conflicting_company(company, company_of(other)):
                raise ValidationError(
                    _("Referința internă '%(code)s' există deja la produsul '%(name)s'!")
                    % {"code": product.default_code, "name": other.display_name}
                )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # index pe default_code (campul standard e stored dar neindexat) — necesar
    # ca search-ul din constrangere sa fie rapid pe baze mari
    default_code = fields.Char(index=True)

    @api.constrains("default_code", "active", "company_id")
    def _check_default_code_unique(self):
        _check_unique_default_code(self, lambda p: p.company_id)

    @api.model
    def get_new_code(self, categ, default_code, barcode):
        values = {}
        if default_code in [False, "/", "auto"] or self.env.context.get("force_code", False):
            if categ.sequence_id:
                default_code = categ.sequence_id.next_by_id()
                values["default_code"] = default_code

        if not barcode or barcode == "/" or barcode == "auto":
            if categ.generate_barcode:
                if not default_code or categ.barcode_random:
                    default_code = "%0.10d" % random.randint(0, 999999999999)  # noqa UP031
                barcode = "".join([s for s in default_code if s.isdigit()])
                barcode = categ.prefix_barcode[:2] + barcode.zfill(10) + "0"
                barcode = self.env["barcode.nomenclature"].sanitize_ean(barcode)
                # verificare unicitate cod de bare
                if self.env["product.template"].search([("barcode", "=", barcode)]):
                    barcode = False
                values["barcode"] = barcode

        return values

    def button_new_code(self):
        for product in self:
            values = self.env["product.template"].get_new_code(product.categ_id, product.default_code, product.barcode)
            product.write(values)
            product.product_variant_ids.write(values)

    # # codificare automata  la creare
    # @api.model_create_multi
    # def create(self, vals_list):
    #     create_product_product = self.env.context.get("create_product_product", False)
    #     product_product_with_code = self.env.context.get("product_procut_with_code", False)
    #     if not create_product_product and not product_product_with_code:
    #         for vals in vals_list:
    #             if "default_code" not in vals or vals["default_code"] in [
    #                 "/",
    #                 "",
    #                 False,
    #             ]:
    #                 categ_id = vals.get("categ_id")
    #                 if categ_id:
    #                     categ = self.env["product.category"].browse(categ_id)
    #                     default_code = vals.get("default_code", False)
    #                     barcode = vals.get("barcode", False)
    #                     attribute_lines_ids = vals.get("attribute_line_ids", [])
    #                     pass_code_for_template = False
    #                     for attribute_lines_id in attribute_lines_ids:
    #                         attribute_id = attribute_lines_id[2].get("attribute_id", False)
    #                         if attribute_id:
    #                             attribute = self.env["product.attribute"].browse(attribute_id)
    #                             if attribute and attribute.create_variant in ["always", "dynamic"]:
    #                                 if len(attribute_lines_id[2].get("value_ids")) > 1:
    #                                     pass_code_for_template = True
    #                                     break
    #                     if pass_code_for_template:
    #                         continue
    #                     values = self.env["product.template"].get_new_code(categ, default_code, barcode)
    #                     vals.update(values)
    #
    #     return super().create(vals_list)

    def force_new_code(self):
        self.with_context(force_code=True).button_new_code()

    @api.model
    def show_not_unique(self):
        sql = """
             SELECT id FROM
              (SELECT *, count(*)
                   OVER   (PARTITION BY  default_code, active, company_id) AS count
                    FROM product_template)
               tableWithCount
              WHERE tableWithCount.count > 1;
        """
        self.env.cr.execute(sql)
        product_ids = [x[0] for x in self.env.cr.fetchall()]

        action = self.env["ir.actions.actions"]._for_xml_id("product.product_template_action")
        action["domain"] = [("id", "in", product_ids)]
        action["context"] = self.env.context
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("default_code", "active")
    def _check_default_code_unique(self):
        _check_unique_default_code(self, lambda p: p.product_tmpl_id.company_id)

    # la crearea unei variante nu se codifica automat si produsul
    # codificare automata  la creare
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            categ_id = vals.get("categ_id")
            # categoria in product.product apare la crearea din campuri legate de product.product, ex pe linie de vanzare
            if categ_id:
                categ = self.env["product.category"].browse(categ_id)
                default_code = vals.get("default_code", False)
                barcode = vals.get("barcode", False)
                values = self.env["product.template"].get_new_code(categ, default_code, barcode)
                vals.update(values)
            elif "product_tmpl_id" in vals and vals.get("product_tmpl_id"):
                # daca se creaza variante din tempalte ele nu o sa aiba categorie asa ca testam pe template daca are categorie de generare coduri
                template = self.env["product.template"].browse(vals.get("product_tmpl_id"))
                force_code_template = False
                if (
                    template.attribute_line_ids and len(vals_list) == 1 and not template.default_code
                ):  # daca sunt atribute si se genereaza o singura varianta o sa incerce sa faca sanitize si se sterge referinta
                    force_code_template = True
                categ = template.categ_id
                ignore_code_template = False
                dynamic_attributes = template.attribute_line_ids.filtered(
                    lambda x: x.attribute_id.create_variant == "dynamic"
                )
                if any(len(dynamic_attribute.value_ids) > 1 for dynamic_attribute in dynamic_attributes):
                    ignore_code_template = True
                if categ:  # nu cred ca poate sa fie fata dar prefer sa nu aflu
                    if not template.default_code or ignore_code_template:
                        values = self.env["product.template"].get_new_code(
                            categ, vals.get("default_code", False), vals.get("barcode", False)
                        )
                        if force_code_template:
                            template.write(values)
                        vals.update(values)
        return super().create(vals_list)

    def button_new_code(self):
        for product in self:
            values = self.env["product.template"].get_new_code(product.categ_id, product.default_code, product.barcode)
            product.write(values)

    def force_new_code(self):
        self.with_context(force_code=True).button_new_code()

    @api.model
    def show_not_unique(self):
        # product_product nu are coloana company_id (compania vine din template)
        sql = """
             SELECT id FROM
              (SELECT *, count(*)
                   OVER   (PARTITION BY  default_code, active) AS count
                    FROM product_product
                    WHERE default_code IS NOT NULL AND default_code <> '')
               tableWithCount
              WHERE tableWithCount.count > 1;
        """
        self.env.cr.execute(sql)
        product_ids = [x[0] for x in self.env.cr.fetchall()]

        action = self.env["ir.actions.actions"]._for_xml_id("product.product_normal_action")
        action["domain"] = [("id", "in", product_ids)]
        action["context"] = self.env.context
        return action
