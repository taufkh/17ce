# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.depends('check_in', 'check_out')
    def _compute_normal_worked_hours(self):
        for attendance in self:
            employee = attendance.employee_id

            if attendance.check_in and attendance.check_out:
                start_date = start_date_calc = attendance.check_in + timedelta(hours=8)
                end_date = end_date_calc = attendance.check_out + timedelta(hours=8)

                self.env.cr.execute(""" 
                    SELECT MIN(hour_from) AS hour_from, 
                        MAX(hour_to) AS hour_to, 
                        MAX(hour_to) - MIN(hour_from) AS work_hours 
                    FROM resource_calendar_attendance
                    WHERE dayofweek = '%s' AND calendar_id = %s
                """, (start_date.weekday(), employee.resource_calendar_id.id))
                work_schedule = self.env.cr.dictfetchone()

                if not work_schedule.get('work_hours'):
                    attendance.normal_worked_hours = False
                else:
                    min_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=work_schedule['hour_from'])
                    min_end = start_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=work_schedule['hour_to'])

                    max_start = end_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=work_schedule['hour_from'])
                    max_end = end_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=work_schedule['hour_to'])

                    if start_date < min_start:
                        start_date_calc = min_start

                    if end_date > min_end:
                        end_date_calc = min_end

                    day_diff = (end_date.date() - start_date.date()).days
                    first_day_time_value = (end_date_calc - start_date_calc).total_seconds() / 3600.0
                    first_day_time = first_day_time_value > 0 and first_day_time_value or 0

                    if day_diff > 0:
                        if end_date > max_end:
                            day_diff_time = first_day_time + ((day_diff - 1) * work_schedule['work_hours']) + max_end.hour - work_schedule['hour_from']
                        elif end_date < max_start:
                            day_diff_time = first_day_time + ((day_diff - 1) * work_schedule['work_hours'])
                        else:
                            delta = end_date - max_start
                            day_diff_time = first_day_time + ((day_diff - 1) * work_schedule['work_hours']) + (delta.total_seconds() / 3600.0)

                        attendance.normal_worked_hours = day_diff_time
                    else:
                        attendance.normal_worked_hours = first_day_time
            else:
                attendance.normal_worked_hours = False

    @api.depends('check_in', 'check_out')
    def _compute_overtime_worked_hours(self):
        for attendance in self:
            employee = attendance.employee_id

            if attendance.check_in and attendance.check_out:
                start_date = start_date_calc = attendance.check_in + timedelta(hours=8)

                self.env.cr.execute(""" 
                    SELECT MIN(hour_from) AS hour_from
                    FROM resource_calendar_attendance
                    WHERE dayofweek = '%s' AND calendar_id = %s
                """, (start_date.weekday(), employee.resource_calendar_id.id))
                work_schedule = self.env.cr.dictfetchone()

                if not work_schedule.get('hour_from'):
                    attendance.overtime_worked_hours = False
                else:
                    min_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=work_schedule['hour_from'])
                    start_early = 0

                    if start_date < min_start:
                        start_early = (min_start - start_date).total_seconds() / 3600.0

                    attendance.overtime_worked_hours = attendance.worked_hours - attendance.normal_worked_hours - start_early
            else:
                attendance.overtime_worked_hours = False

    normal_worked_hours = fields.Float(compute='_compute_normal_worked_hours', string='Normal Work Hours', store=True)
    overtime_worked_hours = fields.Float(compute='_compute_overtime_worked_hours', string='Overtime Work Hours', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)