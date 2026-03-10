{
    'name': 'ODES Cashflow Forecast',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Customize',
    'author': "SGEEDE",
    'website': "https://www.sgeede.com",
    'summary': 'ODES Cashflow Forecast',
    'description': """
Odes Cashflow Forecast.
===========================
Module for cashflow forecast report.

**Installed on :** IP_SERVER | DB NAME :
    """,
    'depends': ['odes_accounting', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',  
        'wizard/odes_cashflow_forecast_wizard_views.xml',    
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
