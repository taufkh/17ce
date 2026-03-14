# -*- coding: utf-8 -*-
import json
import base64
from datetime import datetime, timedelta
from odoo import http, models, fields, _
from odoo.http import request
from odoo.tools.misc import get_lang, DEFAULT_SERVER_DATE_FORMAT

class iMinHrApi(http.Controller):
    def is_checked_in_today(self, recordTime, memberId):
        parsed_record_time = datetime.strptime(recordTime, "%Y-%m-%d %H:%M:%S")
        yesterday_record_time = parsed_record_time - timedelta(days=1)

        """
        Because odoo save time on UTC-0 and our date is UTC-8, so the start of the day of today will be 00:00:00 - 8 hours = 16:00:00
        And the end of today will be 24:00:00 - 8 hours = 15:59:59 
        """
        start_of_day = yesterday_record_time.strftime('%Y-%m-%d') + ' 16:00:00'
        end_of_day = parsed_record_time.strftime('%Y-%m-%d') + ' 15:59:59'

        attendance_today_id = request.env['hr.attendance'].sudo().search([('check_in', '>=', start_of_day), ('check_in', '<=', end_of_day), ('employee_id.member_id', '=', memberId)])
        
        if attendance_today_id:
            return attendance_today_id
        else:
            return False

    def update_check_out(self, attendance, rec_time):
        formatted_record_time = datetime.strptime(rec_time, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)

        attendance.write({
            'check_out': formatted_record_time
        })

    def create_new_attendance(self, employee_id, record_time):
        formatted_record_time = datetime.strptime(record_time, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)

        request.env['hr.attendance'].sudo().create({
            'employee_id': employee_id.id,
            'check_in': str(formatted_record_time)
        })
        return True
    
    def prepare_log_values(self, log):
        return {
            'name': log.get('userName', False),
            'department': log.get('department', False),
            'device_name': log.get('deviceName', False),
            'device_sn': log.get('deviceSN', False),
            'has_mask': log.get('hasMask', False),
            'md_code': log.get('mdCode', False),
            'member_id': log.get('memberId', False),
            'recognize_mode': log.get('recognizeMode', False),
            'record_time': log.get('recordTime', False),
            'status': log.get('status', False),
            'temperature': log.get('temperature', False)
        }

    @http.route('/imin/api/webhook_get', type='json', auth='public', website=True)
    def webhook_get(self, **kwargs):
        res = json.loads(request.httprequest.data)
        
        # res = request.get('jsonrequest')
        if res:
            log_values = self.prepare_log_values(res)
            state = 'failed'

            employee_id = request.env['hr.employee'].sudo().search([('member_id', '=', log_values['member_id'])])
            if employee_id:
                has_checked_in_today = self.is_checked_in_today(log_values['record_time'], log_values['member_id'])
                if has_checked_in_today:
                    self.update_check_out(has_checked_in_today, log_values['record_time'])
                    state = 'success'
                else:
                    self.create_new_attendance(employee_id, log_values['record_time'])
                    state = 'success'
            
            log_values['state'] = state
            request.env['imin.hr.webhook.log'].create(log_values)

        return True