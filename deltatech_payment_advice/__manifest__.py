# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Deltatech Payment Advice",
    "summary": "Remittance advice sent to suppliers based on batch payments",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Accounting & Finance",
    "depends": ["account_batch_payment"],
    "data": [
        "report/payment_advice_report.xml",
        "report/payment_advice_templates.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
