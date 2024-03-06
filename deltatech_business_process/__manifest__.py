# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Business process",
    "summary": "Business process",
    "version": "17.0.1.0.6",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Generic Modules/Other",
    "depends": ["base", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/business_area_view.xml",
        "views/business_role_view.xml",
        "views/business_development_type_view.xml",
        "views/business_transaction_view.xml",
        "views/business_project_view.xml",
        "views/business_process_view.xml",
        "views/business_process_step_view.xml",
        "views/business_development_view.xml",
        "views/business_process_test_view.xml",
        "views/business_process_step_test_view.xml",
        "views/business_issue_view.xml",
        "report/business_process_report_view.xml",
        "report/business_process_test_report_view.xml",
        "data/ir_sequence_data.xml",
        "wizard/export_business_process_view.xml",
        "wizard/import_business_process_view.xml",
    ],
    "development_status": "Beta",
    "images": ["static/description/main_screenshot.png"],
    "maintainers": ["dhongu"],
    "application": True,
}
