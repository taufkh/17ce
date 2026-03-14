# -*- coding: utf-8 -*-
import json
import base64
import requests
import urllib.parse
from odoo import api, fields, models, _

TOKEN_URL = 'https://officemateapi.imin.sg/api/token'
API_URL = 'https://officemateapi.imin.sg/api/v1'

class IminFetchEmployee(models.TransientModel):
    _name = 'imin.fetch.employee'
    _description = 'iMin Fetch Employees'

    def action_confirm(self):
        department_obj = self.env['imin.hr.department']
        employee_obj = self.env['imin.hr.employee']
        company = self.env.user.company_id
        token_res = company.get_token()

        if token_res.get('code') == 0:
            url_params = urllib.parse.urlencode({
                'token': token_res['data']['token']
            })
            departments = department_obj.search([])

            for department in departments:
                data = {
                    'param': {
                        'departmentId': department.imin_id
                    },
                    'public': {
                        'method': 'employee.list.get',
                        'format': 'json',
                        'token': token_res['data']['token'],
                        'version': 'v1.0'
                    }
                }
                data = json.dumps(data)
                headers = {
                    'Content-type': 'text/plain; charset=utf-8'
                }
                res = requests.post(API_URL, data=data, headers=headers)
                res_values = res.json()

                if res_values.get('code') == 0:
                    employees = res_values['data']['list']
                    for employee in employees:
                        employee_exist = employee_obj.search_count([('imin_id', '=', employee['id'])])

                        if not employee_exist:
                            if employee['pic']:
                                pic = base64.b64encode(requests.get(employee['pic']).content)
                            else:
                                pic = False

                            employee_department = department_obj.search([('imin_id', '=', employee['departmentId'])], limit=1)
                            create_time = employee['createTime'].split('.')[0]
                            update_time = employee['updateTime'].split('.')[0]

                            employee_obj.create({
                                'name': employee['name'],
                                'department_id': employee_department.id,
                                'email': employee['email'],
                                'date': employee['entryTime'],
                                'member_type': employee['memberType'],
                                'mobile': employee['mobile'],
                                'gender': employee['sex'],
                                'pic': pic,
                                'position': employee['position'],
                                'tel_area_code': employee['telAreaCode'],
                                'imin_id': employee['id'],
                                'imin_org_id': employee['orgId'],
                                'imin_department_id': employee['departmentId'],
                                'ext_number': employee['extNumber'],
                                'staff_id': employee['jobNumber'],
                                'org_queue': employee['orgQueue'],
                                'imin_create_time': create_time,
                                'imin_update_time': update_time 
                            })

        return res