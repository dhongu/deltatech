# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

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
