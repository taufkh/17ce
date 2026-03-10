# -*- coding: utf-8 -*-
{
    'name': 'ODES HR Attendance',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Custom',
    'summary': 'ODES HR Attendance',
    'author': 'SGEEDE',
    'description': '''
        Customization for ODES HR Attendance.
    ''',
    'depends': ['hr', 'hr_attendance', 'hr_holidays'],
    'data': [
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml'
    ],
    'demo': [],
}