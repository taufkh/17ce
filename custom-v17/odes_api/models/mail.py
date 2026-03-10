# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import re
from uuid import uuid4

from odoo import _, api, fields, models, modules, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import ormcache, formataddr
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
import requests
import json

try:
    import html2text
except Exception:  # pragma: no cover - optional dependency fallback
    html2text = None

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext


def to_plain_text(raw_html):
    if html2text:
        handler = html2text.HTML2Text()
        handler.ignore_links = True
        return handler.handle(raw_html or "")
    return cleanhtml(raw_html or "")

class Channel(models.Model):
    _inherit = 'discuss.channel'


    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *, message_type='notification', **kwargs):
        user_obj = self.env['res.users']
        serverToken = 'AAAAQZwUr4o:APA91bGISxxHZxqY1VxUjWJ_j3Ax8tTlmLt1LvQYnxdhiQBgnZpZi9rL5I7evH_ztqil-O09BXWtT5oRdqjHzb3wbB_vjG6I9Jax9mYLwh9UtFfA6K1triK3cnebGH0T3qEHr9hWcvnc'
        message = super(Channel, self.with_context(mail_create_nosubscribe=True)).message_post(message_type=message_type,  **kwargs)
        if message_type == 'comment' and message.model == 'discuss.channel':
            for channel in message.channel_ids:
                for mini_channel in channel.channel_last_seen_partner_ids:
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    partner = mini_channel.partner_id
                    user = user_obj.search([('partner_id','=',partner.id)],limit=1)
                    deviceToken = user.registration_id
                    login = user.login
                    password = 'mobile0_treatment$'+str(user.id)
                    base_url = base_url + '/api/login-user?' + 'email=' + str(login) + '&password=' + str(password) + '&redirect_type=notification'
                    base_url = base_url.replace("http://","https://")
                    if partner!=message.author_id and deviceToken:
                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': 'key=' + str(serverToken),
                          }
                        html_2_text = message.body
                        if message.author_id:
                            body = {
                                    'to':deviceToken,
                                    'priority': 'high',
                                    'notification': {'title': 'Message from ' + message.author_id.name,
                                                        'body': to_plain_text(html_2_text),
                                                        'content_available':True,
                                                        'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                                                        },
                                    'data' : {'redirection' : str(base_url)}
                                    }
                            response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
        return message


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model_create_multi
    def create(self, vals_list):
        serverToken = 'AAAAQZwUr4o:APA91bGISxxHZxqY1VxUjWJ_j3Ax8tTlmLt1LvQYnxdhiQBgnZpZi9rL5I7evH_ztqil-O09BXWtT5oRdqjHzb3wbB_vjG6I9Jax9mYLwh9UtFfA6K1triK3cnebGH0T3qEHr9hWcvnc'
        result = super(MailActivity, self).create(vals_list)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for data in result:
            user = data.user_id
            deviceToken = user.registration_id
            login = user.login
            password = 'mobile0_treatment$'+str(user.id)
            base_url = base_url + '/api/login-user?' + 'email=' + str(login) + '&password=' + str(password) + '&redirect_type=notification'
            base_url = base_url.replace("http://","https://")
            if deviceToken:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + str(serverToken),
                  }
                noted = data.note
                if noted:
                    noted = cleanhtml(noted)
                summary = data.summary or noted
                html_2_text = summary or 'New'
                body = {
                        'to':deviceToken,
                        'priority': 'high',
                        'notification': {'title': data.activity_type_id.name or 'Message',
                                            'body': to_plain_text(html_2_text),
                                            'content_available':True,
                                            'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                                            },
                        'data' : {'redirection' : str(base_url)}
                        }
                response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
        
        return result
