
{
    'name': 'ODES HR Custom V2',
'version': '17.0.1.0.0',    'license': 'LGPL-3',
    'category': 'Customize',
    'summary': 'ODES Project',
    'author': "ODES",
    'website': "https://www.ODES.com",
    'description': """
Customization for ODES HR Project V2
    """,
    'depends': [
    'odes_custom',
    'hr',
    'hr_payroll',
    'l10n_sg_hr_payroll',
    'sg_allocate_leave',
    'sg_expense_maxcap',
    'sg_expense_payroll',
    'sg_holiday_extended'
    ,'sg_hr_employee',
    'sg_hr_holiday',
    'sg_hr_payslip_YTD',
    'sg_hr_report',
    'sg_expire_leave',
    'sg_holiday_config',
    'sg_leave_extended',
    'sg_bank_reconcilation_report'
    ,'sg_appendix8a_report',
    'sg_bank_reconcile',
    'sg_cimb_report',
    'sg_dbs_giro',
    'sg_income_tax_report',
    'sg_document_expiry',
    'sg_ir21',
    'sg_ocbc_report',
    'sg_ow_aw_cpf',
    'sg_report_letter_undertaking',
    'sg_account_config',
    'sg_expense_config',
    'sg_leave_constraints',
    'sg_payroll_constraints',
    'hr_holidays',
    'hr_contract',
    'hr_expense'],
    'data': [ 
       

       # 'views/res_config_setting_views.xml',
       # 'views/hr_views.xml',
       # 'report/report_payslip_templates.xml',
       # 'report/report_leave_balance.xml',
       'security/ir.model.access.csv',
       'security/security.xml',
       'views/revert_xml.xml',
       'views/hr_views_2.xml',
       'views/hr_holidays_views.xml',
       'views/hr_contract_views.xml',
       # Community-safe: allocation form xpath targets changed in v17.
       # 'views/hr_leave_allocation_views.xml',
       'views/hr_department_views.xml',
    ],
    #
    # 'demo': [
    # ],
    'installable': True,
    'auto_install': False
}
