# ©  2025 Terrabit
#              Voicu Stefan <stefan(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

{
    "name": "Product Website Visibility Score",
    "summary": "Scor colorat de vizibilitate a produsului pe website (semafor + defalcare pe criterii)",
    "version": "19.0.1.0.1",
    "author": "Terrabit, Voicu Stefan",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Website/eCommerce",
    "depends": ["website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/product_visibility_criterion_data.xml",
        "views/visibility_criterion_view.xml",
        "views/product_template_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
