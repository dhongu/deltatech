# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import random
import re

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL


class ProductCategory(models.Model):
    _inherit = "product.category"

    sequence_id = fields.Many2one("ir.sequence", string="Code Sequence")
    generate_barcode = fields.Boolean()
    prefix_barcode = fields.Char(
        default="20",
        size=2,
        help="Prefixes 20-29 are reserved by GS1 for internal use; 40-44 belong to GS1 Germany.",
    )
    barcode_random = fields.Boolean(default=True)
    barcode_source = fields.Selection(
        [("internal", "Internal prefix"), ("gs1", "GS1 company prefix")],
        default="internal",
        required=True,
        help="Internal prefix: the barcode is built from the prefix and the internal reference (or a random number).\n"
        "GS1 company prefix: the barcode is the next free GTIN-13 in the range of the GS1 company prefix.",
    )
    gs1_company_prefix = fields.Char(
        string="GS1 Company Prefix",
        help="Company prefix received from GS1 (e.g. 594xxxx). The GTIN-13 codes are allocated in its range.",
    )
    gs1_available_count = fields.Integer(string="Free GTIN Codes", compute="_compute_gs1_available_count")

    @api.constrains("barcode_source", "gs1_company_prefix")
    def _check_gs1_company_prefix(self):
        for categ in self.filtered(lambda c: c.barcode_source == "gs1"):
            prefix = categ.gs1_company_prefix or ""
            if not prefix.isdigit() or not 6 <= len(prefix) <= 11:
                raise ValidationError(self.env._("The GS1 company prefix must have between 6 and 11 digits."))

    @api.depends("barcode_source", "gs1_company_prefix")
    def _compute_gs1_available_count(self):
        template = self.env["product.template"]
        for categ in self:
            prefix = categ.gs1_company_prefix or ""
            if categ.barcode_source != "gs1" or not prefix.isdigit() or not 6 <= len(prefix) <= 11:
                categ.gs1_available_count = 0
                continue
            capacity = 10 ** (12 - len(prefix))
            last_reference = template._get_gs1_last_reference(prefix)
            categ.gs1_available_count = capacity - 1 - last_reference if last_reference >= 0 else capacity


class ProductTemplate(models.Model):
    _inherit = "product.template"

    _name_code_unique = models.Constraint(
        "unique (default_code,active,company_id)",
        "Internal Reference already exists !",
    )

    @api.model
    def _is_code_used(self, code):
        # se cauta in toate companiile, inclusiv printre produsele arhivate
        return bool(
            self.env["product.product"]
            .sudo()
            .with_context(active_test=False)
            .search_count([("default_code", "=", code)], limit=1)
        )

    @api.model
    def _sync_code_sequence(self, sequence):
        """Muta secventa peste cel mai mare numar deja folosit cu prefixul/sufixul ei.

        Contorul secventei nu stie de codurile create pe alte cai (importuri de catalog,
        renumerotari, coduri scrise manual), asa ca poate propune coduri deja folosite.
        """
        if sequence.use_date_range:
            return
        prefix, suffix = sequence._get_prefix_suffix()
        pattern = "^" + re.escape(prefix) + "([0-9]{1,18})" + re.escape(suffix) + "$"
        query = SQL(
            "SELECT max(substring(default_code FROM %s)::bigint) FROM product_product WHERE default_code ~ %s",
            pattern,
            pattern,
        )
        self.env.cr.execute(query)
        max_number = self.env.cr.fetchone()[0] or 0
        if max_number >= sequence.number_next_actual:
            sequence.sudo().write({"number_next_actual": max_number + 1})

    @api.model
    def _get_free_code(self, sequence):
        code = sequence.next_by_id()
        if code and self._is_code_used(code):
            self._sync_code_sequence(sequence)
            code = sequence.next_by_id()
        return code

    @api.model
    def _get_gs1_last_reference(self, prefix):
        """Cel mai mare numar de articol folosit in plaja prefixului GS1 (-1 daca plaja e goala).

        Se cauta in codurile de bare ale variantelor (inclusiv arhivate) si ale ambalajelor.
        """
        pattern = f"^{prefix}([0-9]{{{12 - len(prefix)}}})[0-9]$"
        query = SQL(
            """SELECT max(substring(barcode FROM %(pattern)s)::bigint) FROM (
                   SELECT barcode FROM product_product WHERE barcode ~ %(pattern)s
                   UNION ALL
                   SELECT barcode FROM product_uom WHERE barcode ~ %(pattern)s
               ) AS codes""",
            pattern=pattern,
        )
        self.env.cr.execute(query)
        last_reference = self.env.cr.fetchone()[0]
        return -1 if last_reference is None else last_reference

    @api.model
    def _get_free_gs1_barcode(self, prefix):
        """Urmatorul GTIN-13 liber din plaja prefixului GS1 al companiei."""
        self.env["product.product"].flush_model(["barcode"])
        self.env["product.uom"].flush_model(["barcode"])
        # doua produse create simultan nu trebuie sa primeasca acelasi cod
        self.env.cr.execute(SQL("SELECT pg_advisory_xact_lock(hashtext(%s))", "gs1_gtin:" + prefix))
        reference = self._get_gs1_last_reference(prefix) + 1
        reference_length = 12 - len(prefix)
        if reference >= 10**reference_length:
            raise UserError(
                self.env._(
                    "All GTIN codes of the GS1 company prefix %(prefix)s are used. Request a new prefix from GS1.",
                    prefix=prefix,
                )
            )
        barcode = prefix + str(reference).zfill(reference_length) + "0"
        return self.env["barcode.nomenclature"].sanitize_ean(barcode)

    @api.model
    def get_new_code(self, categ, default_code, barcode):
        values = {}
        if default_code in [False, "/", "auto"] or self.env.context.get("force_code", False):
            if categ.sequence_id:
                default_code = self._get_free_code(categ.sequence_id)
                values["default_code"] = default_code

        if not barcode or barcode == "/" or barcode == "auto":
            if categ.generate_barcode and categ.barcode_source == "gs1":
                values["barcode"] = self._get_free_gs1_barcode(categ.gs1_company_prefix)
            elif categ.generate_barcode:
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
        self.flush_model(["default_code", "active", "company_id"])
        query = SQL(
            """
             SELECT id FROM
              (SELECT id, count(*)
                   OVER   (PARTITION BY  default_code, active, company_id) AS count
                    FROM product_template)
               tableWithCount
              WHERE tableWithCount.count > 1;
        """
        )
        self.env.cr.execute(query)
        product_ids = [x[0] for x in self.env.cr.fetchall()]

        action = self.env.ref("deltatech_product_code.action_force_new_code")
        action.create_action()

        action = self.env["ir.actions.actions"]._for_xml_id("product.product_template_action")

        action["domain"] = [("id", "in", product_ids)]
        action["context"] = self.env.context
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    # la crearea unei variante nu se codifica automat si produsul
    # codificare automata  la creare
    @api.model_create_multi
    def create(self, vals_list):
        # In 18.0 this guard was absent — the sequence would overwrite any manually set default_code.
        # In 19.0 we preserve the manually set code (behavior kept intentionally).
        for vals in vals_list:
            if "default_code" not in vals or vals["default_code"] in ["/", "", False]:
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
        self.flush_model(["default_code", "active"])
        self.env["product.template"].flush_model(["company_id"])
        # product_product nu are coloana company_id (e related pe template)
        query = SQL(
            """
             SELECT id FROM
              (SELECT pp.id, count(*)
                   OVER   (PARTITION BY  pp.default_code, pp.active, pt.company_id) AS count
                    FROM product_product pp
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id)
               tableWithCount
              WHERE tableWithCount.count > 1;
        """
        )
        self.env.cr.execute(query)
        product_ids = [x[0] for x in self.env.cr.fetchall()]

        action = self.env.ref("deltatech_product_code.action_force_new_code_product")
        action.create_action()

        action = self.env["ir.actions.actions"]._for_xml_id("product.product_variant_action")

        action["domain"] = [("id", "in", product_ids)]
        action["context"] = self.env.context
        return action
