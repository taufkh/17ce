# -*- coding: utf-8 -*-
import json
import requests
import urllib.parse
from odoo import api, fields, models, _

TOKEN_URL = 'https://officemateapi.imin.sg/api/token'
API_URL = 'https://officemateapi.imin.sg/api/v1'

class IminFetchDepartment(models.TransientModel):
    _name = 'imin.fetch.department'
    _description = 'iMin Fetch Departments'

    def action_confirm(self):
        department_obj = self.env['imin.hr.department']
        company = self.env.user.company_id
        token_res = company.get_token()

        if token_res.get('code') == 0:
            url_params = urllib.parse.urlencode({
                'token': token_res['data']['token']
            })

            data = {
                'param': {},
                'public': {
                    'method': 'department.getAll',
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
                root = res_values['data']['rootInfo']
                children = res_values['data']['children']

                root_exist = department_obj.search_count([('imin_id', '=', root['id'])])
                if not root_exist:
                    department_obj.create({
                        'name': root['orgName'],
                        'imin_id': root['id']    
                    })

                for child in children:
                    child_exist = department_obj.search_count([('imin_id', '=', child['id'])])
                    if not child_exist:
                        parent = department_obj.search([('imin_id', '=', child['parentId'])], limit=1)
                        department_obj.create({
                            'name': child['orgName'],
                            'parent_id': parent.id,
                            'imin_id': child['id'],
                            'imin_parent_id': child['parentId']
                        })

        return res