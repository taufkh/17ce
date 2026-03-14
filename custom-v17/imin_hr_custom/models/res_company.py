# -*- coding: utf-8 -*-
import json
import requests
import urllib.parse
import datetime
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, _

TOKEN_URL = 'https://officemateapi.imin.sg/api/token'
API_URL = 'https://officemateapi.imin.sg/api/v1'

class Company(models.Model):
    _inherit = 'res.company'

    def get_token(self):
        for company in self:
            data = {
                'param': {
                    'app_id': company.imin_app_id,
                    'app_secret': company.imin_app_secret
                },
                'public': {
                    'method': 'token.getToken',
                    'format': 'json',
                    'token': '',
                    'version': 'v1.0'
                }
            }
            data = json.dumps(data)
            headers = {
                'Content-type': 'text/plain; charset=utf-8'
            }
            res = requests.post(TOKEN_URL, data=data, headers=headers)
            return res.json()

    def action_set_imin_webhook(self):
        for company in self:
            if not company.imin_app_id:
                raise UserError(_('Please set your iMin App ID!'))
            if not company.imin_app_secret:
                raise UserError(_('Please set your iMin App Secret!'))
            if not company.imin_webhook_url:
                raise UserError(_('Please set your iMin Webhook URL!'))

            token_res = company.get_token()

            if token_res.get('code') == 0:
                url_params = urllib.parse.urlencode({
                    'token': token_res['data']['token']
                })

                data = {
                    'param': {
                        'recordWebhookURL': '%s?%s' % (company.imin_webhook_url, url_params)
                    },
                    'public': {
                        'method': 'common.setRecordWebhook',
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

            return res

    def auto_fill_check_out(self):
        attendance_ids = self.env['hr.attendance'].search([('check_out', '=', False)])
        for i in attendance_ids:
            record_time = i.check_in + timedelta(hours=8)
            check_out = record_time.replace(hour=15, minute=50)

            i.write({
                'check_out': check_out
            })

    imin_app_id = fields.Char('iMin App ID')
    imin_app_secret = fields.Char('iMin App Secret')
    imin_webhook_url = fields.Char('iMin Webhook URL')