{
    "name": "Simple Claims Management",
    "version": "12.0.1.0.0",
    "category": "Customer Relationship Management",
    "author": "OpenERP SA, Terrabit, Dorin Hongu",
    "license": "AGPL-3",
    "website": "https://www.odoo.com",
    "depends": ["sales_team"],
    "data": [
        "views/crm_claim_view.xml",
        "views/crm_claim_menu.xml",
        "security/ir.model.access.csv",
        "report/crm_claim_report_view.xml",
        "data/crm_claim_data.xml",
        "views/res_partner_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "test": ["test/process/claim.yml", "test/ui/claim_demo.yml"],
}
