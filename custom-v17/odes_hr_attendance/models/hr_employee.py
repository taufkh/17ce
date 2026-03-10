# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.osv import expression
from datetime import datetime

class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    def _get_last_attendance(self):
        self.ensure_one()
        return self.env['hr.attendance'].sudo().search(
            [('employee_id', '=', self.id)],
            order='check_in desc, id desc',
            limit=1,
        )

    def _search_hr_attendance_display(self, operator, value):
        negative = operator in expression.NEGATIVE_TERM_OPERATORS
        attendance_obj = self.env['hr.attendance'].sudo()
        leave_obj = self.env['hr.leave'].sudo()

        # In case we have no value
        if not value:
            return expression.TRUE_DOMAIN if negative else expression.FALSE_DOMAIN

        if operator in ['=', '!=']:
            if value == 'attend':
                attendances = attendance_obj.search(['|', ('check_in', '>=', fields.Date.today()), ('check_out', '>=', fields.Date.today())])
                if attendances:
                    return [('id', 'in', attendances.mapped('employee_id').ids)]
                else:
                    return expression.FALSE_DOMAIN

            if value == 'not_attend':
                leaves = leave_obj.search([
                    ('date_from', '<=', fields.Date.today()),
                    ('date_to', '>=', fields.Date.today()),
                    ('state', 'not in', ('cancel', 'refuse'))
                ])
                if leaves:
                    return [('id', 'in', leaves.mapped('employee_id').ids)]
                else:
                    return expression.FALSE_DOMAIN

            if value == 'absent':
                attendances = attendance_obj.search(['|', ('check_in', '>=', fields.Date.today()), ('check_out', '>=', fields.Date.today())])
                leaves = leave_obj.search([
                    ('date_from', '<=', fields.Date.today()),
                    ('date_to', '>=', fields.Date.today()),
                    ('state', 'not in', ('cancel', 'refuse'))
                ])
                employee_ids = attendances.mapped('employee_id').ids + leaves.mapped('employee_id').ids
                return [('id', 'not in', employee_ids)]

        return expression.TRUE_DOMAIN

    def _compute_hr_attendance_display(self):
        for employee in self:
            employee.hr_attendance_display = 'absent'

            holiday = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '<=', fields.Date.today()),
                ('request_date_to', '>=', fields.Date.today()),
                ('state', 'not in', ('cancel', 'refuse'))
            ], order='id desc', limit=1)
            if holiday:
                employee.hr_attendance_display = 'not_attend'
                employee.current_date_leave_id = holiday.holiday_status_id.id
            else:
                employee.current_date_leave_id = False

            last_attendance = employee._get_last_attendance()
            if last_attendance:
                check_in_date = last_attendance.check_in and last_attendance.check_in.date() or False
                check_out_date = last_attendance.check_out and last_attendance.check_out.date() or False

                if employee.attendance_state == 'checked_in':
                    employee.hr_attendance_display = 'attend'
                elif employee.attendance_state == 'checked_out' and check_out_date >= fields.Date.today():
                    employee.hr_attendance_display = 'attend'

    def _compute_attendance_running_work_hours(self):
        for employee in self:
            last_attendance = employee._get_last_attendance()
            check_out_date = last_attendance.check_out and last_attendance.check_out.date() or False

            if employee.attendance_state == 'checked_in':
                employee.attendance_running_work_hours = (fields.Datetime.now() - last_attendance.check_in).total_seconds() / 3600.0
            elif employee.attendance_state == 'checked_out' and (check_out_date == fields.Date.today()):
                employee.attendance_running_work_hours = last_attendance.worked_hours
            else:
                employee.attendance_running_work_hours = False

    def action_view_timesheet(self):
        self.ensure_one()

        return {
            'name': 'Daily Work Report',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'hr.daily.work.report',
            'domain': [('employee_id', '=', self.id)],
            'view_id': self.env.ref('odes_custom.hr_daily_work_report_view_tree').id,
            'context': {'search_default_today_report': 1, 'create': 0, 'edit': 0, 'delete': 0}
        }

    def action_view_calendar(self):
        self.ensure_one()

        action = self.env['ir.actions.actions']._for_xml_id('calendar.action_calendar_event')
        if self.user_partner_id:
            action['context'] = {
                'default_partner_ids': [self.user_partner_id.id]
            }
            action['domain'] = [('id', 'in', self.user_partner_id.meeting_ids.ids)]

        return action

    def action_view_okr(self):
        self.ensure_one()

        return {
            'name': 'OKR Node',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,org',
            'res_model': 'okr.node',
            'domain': [('employee_id', '=', self.id)],     
        }

    hr_attendance_display = fields.Selection([
        ('attend', 'Attend'), 
        ('not_attend', 'Not Attend with Reason'), 
        ('absent', 'Absent')], 
        compute='_compute_hr_attendance_display', 
        search='_search_hr_attendance_display', 
        string='Attendance Display')
    current_date_leave_id = fields.Many2one('hr.leave.type', compute='_compute_hr_attendance_display', string='Current Date Time Off Type')
    last_attendance_check_in = fields.Datetime(compute='_compute_last_attendance_checks', string='Last Check In')
    last_attendance_check_out = fields.Datetime(compute='_compute_last_attendance_checks', string='Last Check Out')
    attendance_running_work_hours = fields.Float(compute='_compute_attendance_running_work_hours', string='Running Work Hours')
    im_status = fields.Char(related='user_id.partner_id.im_status')
    @api.depends('attendance_state')
    def _compute_last_attendance_checks(self):
        for employee in self:
            last_attendance = employee._get_last_attendance()
            employee.last_attendance_check_in = last_attendance.check_in or False
            employee.last_attendance_check_out = last_attendance.check_out or False
