# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

# Field name -> xmlid of the ir.cron it enables/disables. This settings screen
# is meant to be the ONLY place these crons get turned on: they ship
# active=False in data/ir_cron_data.xml, and toggling one of these fields
# writes ir.cron.active directly, instead of requiring a trip to
# Settings > Technical > Automation > Scheduled Actions.
CRON_ACTIVE_FIELDS = {
    "dt_actions_xml_active": "deltatech_actions.ir_cron_delete_xml_attachments",
    "dt_actions_invoice_pdf_active": "deltatech_actions.ir_cron_delete_pdf_attachments_invoice",
    "dt_actions_sale_pdf_active": "deltatech_actions.ir_cron_delete_pdf_attachments_sale_order",
    "dt_actions_picking_pdf_active": "deltatech_actions.ir_cron_delete_pdf_attachments_stock_picking",
    "dt_actions_messages_active": "deltatech_actions.ir_cron_delete_mail_messages",
    "dt_actions_merge_contacts_active": "deltatech_actions.ir_cron_merge_contacts",
    "dt_actions_merge_companies_active": "deltatech_actions.ir_cron_merge_companies",
    "dt_actions_reorder_rules_active": "deltatech_actions.ir_cron_create_missing_reordering_rules",
    "dt_actions_normalize_names_active": "deltatech_actions.cron_normalize_company_names",
}


# Same crons, exposed read/write as their next scheduled run (ir.cron.nextcall),
# so the settings screen answers "when does this actually run?" without a trip to
# Settings > Technical > Automation > Scheduled Actions.
CRON_NEXTCALL_FIELDS = {
    field_name.replace("_active", "_nextcall"): xmlid for field_name, xmlid in CRON_ACTIVE_FIELDS.items()
}


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dt_actions_xml_active = fields.Boolean(string="Enable duplicate XML attachments cleanup")
    dt_actions_invoice_pdf_active = fields.Boolean(string="Enable invoice PDF cleanup")
    dt_actions_sale_pdf_active = fields.Boolean(string="Enable sale order PDF cleanup")
    dt_actions_picking_pdf_active = fields.Boolean(string="Enable AWB label cleanup")
    dt_actions_messages_active = fields.Boolean(string="Enable old messages cleanup")
    dt_actions_merge_contacts_active = fields.Boolean(string="Enable duplicate contacts merge")
    dt_actions_merge_companies_active = fields.Boolean(string="Enable duplicate companies merge")
    dt_actions_reorder_rules_active = fields.Boolean(string="Enable missing reordering rules cron")
    dt_actions_normalize_names_active = fields.Boolean(string="Enable company name normalization")

    dt_actions_xml_nextcall = fields.Datetime(string="Next execution (XML)")
    dt_actions_invoice_pdf_nextcall = fields.Datetime(string="Next execution (invoice PDF)")
    dt_actions_sale_pdf_nextcall = fields.Datetime(string="Next execution (sale order PDF)")
    dt_actions_picking_pdf_nextcall = fields.Datetime(string="Next execution (AWB label)")
    dt_actions_messages_nextcall = fields.Datetime(string="Next execution (messages)")
    dt_actions_merge_contacts_nextcall = fields.Datetime(string="Next execution (contacts merge)")
    dt_actions_merge_companies_nextcall = fields.Datetime(string="Next execution (companies merge)")
    dt_actions_reorder_rules_nextcall = fields.Datetime(string="Next execution (reordering rules)")
    dt_actions_normalize_names_nextcall = fields.Datetime(string="Next execution (company names)")

    @api.model
    def get_values(self):
        res = super().get_values()
        for field_name, xmlid in CRON_ACTIVE_FIELDS.items():
            cron = self.env.ref(xmlid, raise_if_not_found=False)
            res[field_name] = bool(cron and cron.active)
        for field_name, xmlid in CRON_NEXTCALL_FIELDS.items():
            cron = self.env.ref(xmlid, raise_if_not_found=False)
            res[field_name] = cron.sudo().nextcall if cron else False
        return res

    def set_values(self):
        super().set_values()
        for field_name, xmlid in CRON_ACTIVE_FIELDS.items():
            cron = self.env.ref(xmlid, raise_if_not_found=False)
            if cron and cron.active != self[field_name]:
                cron.sudo().active = self[field_name]
        for field_name, xmlid in CRON_NEXTCALL_FIELDS.items():
            cron = self.env.ref(xmlid, raise_if_not_found=False)
            nextcall = self[field_name]
            if cron and nextcall and cron.sudo().nextcall != nextcall:
                cron.sudo().nextcall = nextcall

    # -- Duplicate XML attachments (account_move.cron_clean_xml_attachments) --
    dt_actions_xml_limit = fields.Integer(
        string="Invoices to process (XML)",
        config_parameter="deltatech_actions.xml_limit",
        default=10,
    )
    dt_actions_xml_duplicates = fields.Integer(
        string="Minimum duplicates (XML)",
        config_parameter="deltatech_actions.xml_duplicates",
        default=10,
    )
    dt_actions_xml_max_delete = fields.Integer(
        string="Max attachments to delete per invoice (XML)",
        config_parameter="deltatech_actions.xml_max_delete",
        default=50,
    )
    dt_actions_xml_max_date_days = fields.Integer(
        string="Older than (days, XML)",
        config_parameter="deltatech_actions.xml_max_date_days",
        default=30,
    )
    dt_actions_xml_dry_run = fields.Boolean(
        string="Dry run (XML)",
        config_parameter="deltatech_actions.xml_dry_run",
        default=True,
    )

    # -- Invoice PDF cleanup (account_move.cron_clean_generated_pdfs) --
    dt_actions_invoice_pdf_limit = fields.Integer(
        string="Attachments to delete (invoice PDF)",
        config_parameter="deltatech_actions.invoice_pdf_limit",
        default=5000,
    )
    dt_actions_invoice_pdf_pattern = fields.Char(
        string="Name pattern (invoice PDF)",
        config_parameter="deltatech_actions.invoice_pdf_pattern",
        default="",
    )
    dt_actions_invoice_pdf_max_date_days = fields.Integer(
        string="Older than (days, invoice PDF)",
        config_parameter="deltatech_actions.invoice_pdf_max_date_days",
        default=90,
    )
    dt_actions_invoice_pdf_dry_run = fields.Boolean(
        string="Dry run (invoice PDF)",
        config_parameter="deltatech_actions.invoice_pdf_dry_run",
        default=True,
    )

    # -- Sale order PDF cleanup (sale_order.cron_clean_generated_pdfs) --
    dt_actions_sale_pdf_limit = fields.Integer(
        string="Attachments to delete (sale order PDF)",
        config_parameter="deltatech_actions.sale_pdf_limit",
        default=5000,
    )
    dt_actions_sale_pdf_pattern = fields.Char(
        string="Name pattern (sale order PDF)",
        config_parameter="deltatech_actions.sale_pdf_pattern",
        default="",
    )
    dt_actions_sale_pdf_max_date_days = fields.Integer(
        string="Older than (days, sale order PDF)",
        config_parameter="deltatech_actions.sale_pdf_max_date_days",
        default=90,
    )
    dt_actions_sale_pdf_dry_run = fields.Boolean(
        string="Dry run (sale order PDF)",
        config_parameter="deltatech_actions.sale_pdf_dry_run",
        default=True,
    )

    # -- Picking AWB label cleanup (stock_picking.cron_clean_generated_pdfs) --
    dt_actions_picking_pdf_limit = fields.Integer(
        string="Attachments to delete (AWB label)",
        config_parameter="deltatech_actions.picking_pdf_limit",
        default=5000,
    )
    dt_actions_picking_pdf_pattern = fields.Char(
        string="Name pattern (AWB label)",
        config_parameter="deltatech_actions.picking_pdf_pattern",
        default="",
    )
    dt_actions_picking_pdf_max_date_days = fields.Integer(
        string="Older than (days, AWB label)",
        config_parameter="deltatech_actions.picking_pdf_max_date_days",
        default=180,
    )
    dt_actions_picking_pdf_dry_run = fields.Boolean(
        string="Dry run (AWB label)",
        config_parameter="deltatech_actions.picking_pdf_dry_run",
        default=True,
    )
    dt_actions_picking_pdf_only_done = fields.Boolean(
        string="Only finished deliveries (done)",
        config_parameter="deltatech_actions.picking_pdf_only_done",
        default=True,
    )
    dt_actions_picking_pdf_only_cancel = fields.Boolean(
        string="Only cancelled deliveries",
        config_parameter="deltatech_actions.picking_pdf_only_cancel",
        default=True,
    )

    # -- Old messages cleanup (mail_message.cron_clean_old_messages) --
    dt_actions_messages_limit = fields.Integer(
        string="Messages to delete",
        config_parameter="deltatech_actions.messages_limit",
        default=5000,
    )
    dt_actions_messages_pattern = fields.Char(
        string="Subject pattern (messages)",
        config_parameter="deltatech_actions.messages_pattern",
        default="",
    )
    dt_actions_messages_max_date_days = fields.Integer(
        string="Older than (days, messages)",
        config_parameter="deltatech_actions.messages_max_date_days",
        default=90,
    )
    dt_actions_messages_dry_run = fields.Boolean(
        string="Dry run (messages)",
        config_parameter="deltatech_actions.messages_dry_run",
        default=True,
    )
    dt_actions_messages_exclude_models = fields.Char(
        string="Excluded models (messages, comma-separated SQL LIKE patterns)",
        config_parameter="deltatech_actions.messages_exclude_models",
        default="business.%,project.%,helpdesk.%",
    )

    # -- Duplicate contact / company merge (res_partner) --
    dt_actions_merge_contacts_limit = fields.Integer(
        string="Duplicate contact groups per run",
        config_parameter="deltatech_actions.merge_contacts_limit",
        default=10,
    )
    dt_actions_merge_companies_limit = fields.Integer(
        string="Duplicate company groups per run",
        config_parameter="deltatech_actions.merge_companies_limit",
        default=10,
    )
