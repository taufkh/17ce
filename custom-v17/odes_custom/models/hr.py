# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse

class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    applicant_url = fields.Char(compute='_get_applicant_url', string='Lead Url')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrApplicant, self).create(vals_list)
        records.send_new_email()
        return records

    def _get_applicant_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        second_url = '/web#id='
        third_url = '&view_type=form&model=hr.applicant&action='
        action = self.env["ir.actions.actions"]._for_xml_id("hr_recruitment.crm_case_categ0_act_job")

        for applicant in self:
            full_url = base_url+second_url+str(applicant.id)+third_url+str(action['id'])
            applicant.applicant_url = full_url

    def send_new_email(self):
        mail_obj = self.env['mail.mail']
        for applicant in self:
            email_to = False
            company = applicant.company_id

            if applicant.job_id.user_id.partner_id.email:
                email_to = applicant.job_id.user_id.partner_id.email

            if not email_to:
                continue

            template = self.env.ref('odes_custom.mail_template_hr_apply_job', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(applicant.id, force_send=True, email_values={'email_to': email_to})


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)

        extra_group_id = self.sudo().env.ref('odes_custom.group_ts_extra_columns')
        for employee in self.sudo():
            if 'timesheet_company_ids' in vals and employee.user_id:
                ###iConnexion Timesheet Extra Columns
                if 3 in employee.timesheet_company_ids.ids:
                    extra_group_id.users = [(4, employee.user_id.id)]
                else:
                    extra_group_id.users = [(3, employee.user_id.id)]

        return res

    def update_user_group(self):
        extra_group_id = self.env.ref('odes_custom.group_ts_extra_columns')
        for employee in self.search([('active', '=', True), ('user_id', '!=', False)]):
            ###iConnexion Timesheet Extra Columns
            if 3 in employee.timesheet_company_ids.ids:
                extra_group_id.users = [(4, employee.user_id.id)]
            else:
                extra_group_id.users = [(3, employee.user_id.id)]

    def update_user_image(self):
        for employee in self:
            if employee.image_1920:
                employee.user_id.image_1920 = employee.image_1920

    timesheet_company_ids = fields.Many2many('res.company', 'timesheet_employee_company_rel', 'employee_id', 'company_id', string='Timesheet Companies')


class HrDailyWorkReport(models.Model):
    _name = "hr.daily.work.report"
    _description = "HR Daily Work Report"

    date = fields.Date(string='Date', default=fields.Date.context_today)
    description = fields.Char('Description')

    partner_id = fields.Many2one('res.partner', 'Customer')
    # Keep this model independent from optional product brand modules.
    brand_id = fields.Char('Brand')
    state = fields.Selection([('in_progress', 'In-Progress'), ('done', 'Done'), ('hold', 'Hold')], 'Status')
    remarks = fields.Char('Remarks')

    def _get_employee(self):
        if self.env.user.employee_ids.ids:
            return self.env.user.employee_ids.ids[0]
        return False

    def _get_employee_domain(self):
        user = self.env.user
        if user.has_group('hr_timesheet.group_timesheet_manager'):
            return []
        elif user.has_group('hr_timesheet.group_hr_timesheet_approver'):
            # return ['|', ('id', 'in', user.employee_ids.ids), ('id', 'in', user.employee_ids.child_ids.ids)]
            return ['|', ('id', 'in', user.employee_ids.ids), ('timesheet_company_ids', 'in', user.timesheet_company_ids.ids)]
        else:
            # return [('id', 'in', user.employee_ids.ids)]
            return ['|', ('id', 'in', user.employee_ids.ids), ('timesheet_company_ids', 'in', user.timesheet_company_ids.ids)]

    employee_id = fields.Many2one('hr.employee',string='Employee', default=_get_employee, domain=_get_employee_domain)
