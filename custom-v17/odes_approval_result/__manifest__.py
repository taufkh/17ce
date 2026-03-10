{
    'name': 'ODES Approval Result',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Customize',
    'author': "ODES",
    'website': "https://www.odes.com.sg",
    'summary': 'ODES Approval Result',
    'description': """
Odes Approval ART Result Customization.
===========================
This module is using for customization of Approval ART Customization
    """,
    'depends': ['base', 'approvals'],
    'data': [
        'views/odes_approval_result_views.xml',
        'views/odes_approval_request_views.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
