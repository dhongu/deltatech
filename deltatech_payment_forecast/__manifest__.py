# Copyright (c) 2024-now Terrabit Solutions All Rights Reserved

{
    "name": "Terrabit payment forecast",
    "summary": "Generates a report to estimate payments at a certain date",
    "author": "Terrabit",
    "license": "AGPL-3",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "version": "14.0.0.0.4",
    "depends": ["account", "deltatech_average_payment_period"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/payment_forecast.xml",
        "wizard/payment_forecast_wizard.xml",
    ],
    "development_status": "Beta",
}
