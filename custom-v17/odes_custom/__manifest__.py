{
    'name': 'ODES Custom',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Customize',
    'author': "SGEEDE",
    'website': "https://www.sgeede.com",
    'summary': 'ODES Custom',
    'description': """
McCoy ODES Customization.
===========================
This module is using for customization of McCoy ODES System.

**Installed on :** IP_SERVER | DB NAME :

- 203.127.198.245 | ODES_PRODUCTION

- 203.127.198.229 | ODES_PRODUCTION_COPY
    """,
    # mccoy_custom removed — was blocked (Enterprise dep: ecommerce_theme).
    # MOQ logic in models/sale.py uses safe env check for mccoy.product.moq model.
    'depends': [
        'base', 'mail', 'crm', 'calendar', 'sale_crm', 'sale', 'sale_management',
        'project', 'hr', 'hr_expense', 'hr_recruitment', 'hr_holidays', 'hr_timesheet',
        'mass_mailing', 'account',
        # 'approvals' — not available in Community edition; model code guarded in __init__.py
        # 'odes_poc_website' — view reference already commented out in company_views.xml
    ],

    'data': [
        'security/odes_security.xml',
        'security/ir.model.access.csv',
        'data/odes_data.xml',
        'wizard/odes_crm_lead_history_wizard_views.xml',
        'wizard/odes_revenue_history_wizard_views.xml',
        'wizard/odes_crm_backward_stage_wizard_views.xml',
        'views/crm_lead_views.xml',
        'views/crm_team_views.xml',
        'views/crm_stage_views.xml',
        'views/ir_attachment_views.xml',
        'views/partner_views.xml',
        'views/user_views.xml',
        'views/calendar_views.xml',
        'views/sale_views.xml',
        'views/company_views.xml',
        'views/project_task_views.xml',
        'views/hr_views.xml',
        # v16: odes_dashboard_templates.xml removed — assets are declared in the 'assets' dict below
        'views/odes_dashboard_views.xml',
        'views/odes_crm_stage_views.xml',
        'views/leave_views.xml',
        'views/expense_views.xml',
        'views/application_views.xml',
        'report/sale_report_templates.xml',
        'report/report_sale_order.xml',
        'report/report_sale_order_sgd.xml',
        # Community-safe: expense report xpath targets changed in v17; disabled in this wave.
        # 'report/hr_expense_report.xml',
        'wizard/crm_lead_lost_views.xml',
        'wizard/crm_lead_to_opportunity_views.xml',
        'wizard/odes_crm_pipeline_wizard_views.xml',
        # 'views/approval_request_views.xml',  # disabled: requires 'approvals' (not in Community)
        'views/account_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            # CSS / LESS / SCSS
            'odes_custom/static/src/less/dashboard.less',
            'odes_custom/static/src/css/odes_backend.css',
            # v16: web_gantt is Enterprise-only; scss kept for base styles it contains
            'odes_custom/static/src/scss/web_gantt.scss',
            # 3rd-party libs
            'odes_custom/static/src/lib/highcharts.js',
            'odes_custom/static/src/lib/funnel.js',
            # QWeb templates
            'odes_custom/static/src/xml/dashboard.xml',
            'odes_custom/static/src/xml/dashboard_second.xml',
            # JS
            'odes_custom/static/src/js/backend/dashboard.js',
            'odes_custom/static/src/js/backend/dashboard_second.js',
            'odes_custom/static/src/js/web_lead_funnel_chart.js',
            'odes_custom/static/src/js/views/graph/graph_renderer.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False
}
