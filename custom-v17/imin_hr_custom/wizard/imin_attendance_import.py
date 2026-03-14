# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from datetime import timedelta, date
from os import name
from time import strptime
import xlrd
import base64
import datetime
import logging

_logger = logging.getLogger(__name__)

class IminAttendanceImport(models.TransientModel):
    _name = 'imin.attendance.import'
    _description = 'iMin Attendances Import'

    def action_import(self):
        context = self.env.context
        attendance_file = {'ids': self._context.get('id', [])}
        res = self.read(['attendance_file'])
        res = res and res[0] or {}
        attendance_file['form'] = res
        binary_data = attendance_file['form']['attendance_file']
        attendance_file = base64.decodebytes(binary_data)

        try:
            excel = xlrd.open_workbook(file_contents=attendance_file)
        except xlrd.XLRDError:
            raise UserError(_('File format not supported, please recheck your file.'))
        
        sh = excel.sheet_by_index(0)

        no = 0
        created_attendance_ids = []
        for rx in range(sh.nrows):
            splitted = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
            no += 1
            if no != 1:
                staff_name = splitted[1]
                staff_id = splitted[4]
                employee = self.env['hr.employee'].search([('name', '=', staff_name), ('staff_id', '=', staff_id)], limit=1)
                if not employee:
                    employee = self.env['hr.employee'].create({
                        'name': splitted[1],
                        'staff_id' : splitted[4]
                    })
               
                date_with_day = splitted[5] 
                check_in_hour = splitted[7] 
                check_out_hour = splitted[9] 
                date_only_splitted = date_with_day.split()[0] 
                check_in = str(date_only_splitted + " " + check_in_hour)
                check_out = str(date_only_splitted + " " + check_out_hour)

                if not check_in_hour:
                    _logger.warning("'%s (%s)' has no check in time, hence the record is skipped.", employee.name, employee.staff_id)
                else:
                    parsed_date_check_in = datetime.datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S")
                    yesterday_from_check_in = parsed_date_check_in - timedelta(days=1)

                    start_of_day = yesterday_from_check_in.strftime('%Y-%m-%d') + ' 16:00:00'
                    end_of_day = parsed_date_check_in.strftime('%Y-%m-%d') + ' 15:59:59'

                    has_checked_in = self.env['hr.attendance'].search([('check_in', '>=', start_of_day), ('check_in', '<=', end_of_day), ('employee_id', '=', employee.id)])

                    if not has_checked_in:
                        if not check_out_hour:
                            attendance_id = self.env['hr.attendance'].create({
                                'employee_id' : employee.id,
                                'check_in' : datetime.datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8),
                            })
                            created_attendance_ids.append(attendance_id.id)
                        else:
                            attendance_id = self.env['hr.attendance'].create({
                                'employee_id' : employee.id,
                                'check_in' : datetime.datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8),
                                'check_out' : datetime.datetime.strptime(check_out, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8),
                            })
                            created_attendance_ids.append(attendance_id.id)

        if created_attendance_ids:
           return {
               'name': _('Attendance'),
               'type': 'ir.actions.act_window',
               'view_type': 'form',
               'view_mode': 'tree,form',
               'res_model': 'hr.attendance',
               'domain': [('id', 'in', created_attendance_ids)]
           }

    attendance_file = fields.Binary('Upload File', help="File to import (.xls file format)")