# -*- coding: utf-8 -*-
{
    'name': 'iMin HR Custom',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Custom',
    'summary': 'iMin HR Custom',
    'author': 'SGEEDE',
    'description': '''
        Customization for iMin HR.
    ''',
    'depends': ['base', 'hr_attendance', 'hr'],
    'data': [
        'data/imin_scheduler.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/res_company_views.xml',
        'views/imin_hr_webhook_log_views.xml',
        'views/imin_hr_department_views.xml',
        'views/imin_hr_employee_views.xml',
        'wizard/imin_attendance_import_views.xml',
        'wizard/imin_fetch_department_views.xml',
        'wizard/imin_fetch_employee_views.xml'
    ],
    'demo': [],
}