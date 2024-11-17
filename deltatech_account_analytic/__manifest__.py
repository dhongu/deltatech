# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Account Analytic",
    "summary": "Analytic lines enhancements",
    "version": "16.0.0.0.3",
    "author": "Terrabit, Dan Stoica",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Accounting & Finance",
    "depends": ["account", "analytic", "sale", "purchase"],
    "data": [
        "views/res_config_settings.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/account_analytic_default.xml",
        "views/account_analytic_line.xml",
        "views/account_analytic_split_template.xml",
        "views/account_analytic_split.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["danila12"],
}
