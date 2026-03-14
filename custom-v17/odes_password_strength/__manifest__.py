# -*- coding: utf-8 -*- 

{
    'name': 'Odes Password Strength',
    'category': 'Hidden',
'version': '17.0.1.0.0',    'author': "SGEEDE",
    'website': "https://www.sgeede.com",
    'description':
        """
Odes Password Strength.
===========================

This module allows admin to set company-level password security requirements and enforces them on the user.

It contains features such as:

- Password expiration days
- Password length requirement
- Password minimum number of lowercase letters
- Password minimum number of uppercase letters
- Password minimum number of numbers
- Password minimum number of special characters
- Password strength estimation



**Installed on :** IP_SERVER | DB NAME :

- 203.127.198.245 | ODES_PRODUCTION

- 203.127.198.229 | ODES_PRODUCTION_COPY
        """,
    'depends': ['base','web', 'auth_signup', 'odes_master_password'],
    'auto_install': True,
    'data': [
       'security/ir.model.access.csv',
       'security/res_users_pass_history.xml',
       
       
       'views/auth_signup_login_templates.xml',
        'views/res_company_view.xml',
        
    ],
    'assets': {
        # CheckPassword.js / PasswordStrength.js are plain functions called via
        # onkeyup attributes in the signup QWeb template — load in both scopes.
        'web.assets_backend': [
            'odes_password_strength/static/src/js/CheckPassword.js',
            'odes_password_strength/static/src/js/PasswordStrength.js',
            'odes_password_strength/static/src/css/cssfile.css',
        ],
        'web.assets_frontend': [
            'odes_password_strength/static/src/js/CheckPassword.js',
            'odes_password_strength/static/src/js/PasswordStrength.js',
            'odes_password_strength/static/src/css/cssfile.css',
        ],
        # signup_policy.js used odoo.define() with auth_password_policy (removed
        # in v16 — merged into web core).  File archived as .legacy.
    },
    'license': 'LGPL-3',
}
