# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse
from odoo.addons.hr_holidays.models.hr_leave import HolidaysRequest


class HrLeave(models.Model):
    _inherit = "hr.leave"

    is_manager = fields.Boolean('Manager Approve', default=False)
    is_finance = fields.Boolean('Finance Approve', default=False)
    is_director = fields.Boolean('Director Approve', default=False)

    approver_id = fields.Many2one('res.users','Approver')

    date_approve = fields.Datetime('Approved Date')


    @api.model_create_multi
    def create(self, vals_list):
        holidays = super(HrLeave, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

        for holiday in holidays:
            approver = holiday.get_approver_user('manager')
            holiday.approver_id = approver

        return holidays


    def write(self, values):
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.is_superuser()

        # if not is_officer:
            # if any(hol.date_from.date() < fields.Date.today() for hol in self):
                # raise UserError(_('You must have manager rights to modify/validate a time off that already begun'))

        employee_id = values.get('employee_id', False)
        if not self.env.context.get('leave_fast_create'):
            if values.get('state'):
                self._check_approval_update(values['state'])
                if any(holiday.validation_type == 'both' for holiday in self):
                    if values.get('employee_id'):
                        employees = self.env['hr.employee'].browse(values.get('employee_id'))
                    else:
                        employees = self.mapped('employee_id')
                    self._check_double_validation_rules(employees, values['state'])
            if 'date_from' in values:
                values['request_date_from'] = values['date_from']
            if 'date_to' in values:
                values['request_date_to'] = values['date_to']
        result = super(HolidaysRequest, self).write(values)
        if not self.env.context.get('leave_fast_create'):
            for holiday in self:
                if employee_id:
                    holiday.add_follower(employee_id)
        return result

    HolidaysRequest.write = write

    def action_approve_warning(self, approver):      
        if approver.is_finance:
            raise UserError(_('The leave is waiting "Finance" to approve'))
        elif approver.is_director:
            raise UserError(_('The leave is waiting "Director" to approve'))
        else:
            raise UserError(_('The leave is waiting "Manager" to approve'))


    def action_approve(self):
        approver = False
        ###IF Finance, auto able to approve
        if self.env.user.is_finance and not self.is_finance:
            approver = self.get_approver_user('finance')
        elif not self.is_manager:
            approver = self.get_approver_user('manager')
        elif not self.is_finance:
            approver = self.get_approver_user('finance')
        elif not self.is_director:
            approver = self.get_approver_user('director')
        if not approver:
            raise UserError(_('No Approver exist, Please Reset to Draft and Re-Submit to Manager'))        

        if self.env.user != approver:
            self.action_approve_warning(approver)

        ###IF Finance, auto able to approve ++ or If Director, also auto approve
        if self.env.user.is_finance and not self.is_finance or self.env.user.is_director:
            date_now = datetime.now()
            leave_start_date = self.date_from

            ## Finance can validate without Director if already past today date
            if date_now > leave_start_date or self.env.user.is_director:
                self.is_manager = True
                self.is_finance = True
                self.is_director = True
                new_approver = approver
                self.write({'state': 'validate', 'date_approve': date_now})
            else:
                self.is_manager = True
                self.is_finance = True
                new_approver = self.get_approver_user('director')

            ## Add Finance into followers to be able receive email
            reg = { 
               'res_id': self.id, 
               'res_model': 'hr.leave', 
               'partner_id': self.env.user.partner_id.id, 
            }
            
            if not self.env['mail.followers'].search([('res_id','=',self.id),('res_model','=','hr.leave'),('partner_id','=',self.env.user.partner_id.id)]): 
                follower_id = self.env['mail.followers'].sudo().create(reg)

        elif not self.is_manager:
            self.is_manager = True
            new_approver = self.get_approver_user('finance')
        elif not self.is_finance:
            self.is_finance = True
            new_approver = self.get_approver_user('director')
        elif not self.is_director:
            self.is_director = True
            date_now = datetime.now()

            new_approver = approver
            self.write({'state': 'validate', 'date_approve': date_now})

        
        self.approver_id = new_approver.id
        self.activity_update()



    def get_approver_user(self, user_type):
        users = self.env['res.users']
        user_obj = self.env['res.users'].sudo()
        if user_type == 'all':
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.employee_id.user_id.id)], limit=1)
            manager_user = employee.parent_id.user_id
            if manager_user:
                users |= manager_user

            finance_users = user_obj.search([('is_finance', '=', True)], limit=1)
            if finance_users:
                users |= finance_users

            director_users = user_obj.search([('is_director', '=', True)], limit=1)
            if director_users:
                users |= director_users

        elif user_type == 'manager':
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.employee_id.user_id.id)], limit=1)
            manager_user = employee.parent_id.user_id
            if manager_user:
                users |= manager_user

        elif user_type == 'finance':
            finance_users = user_obj.search([('is_finance', '=', True)], limit=1)
            if finance_users:
                users |= finance_users

        elif user_type == 'director':
            director_users = user_obj.search([('is_director', '=', True)], limit=1)
            if director_users:
                users |= director_users

        return users