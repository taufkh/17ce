# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime

class IminHrWebhookLog(models.Model):
    _name = "imin.hr.webhook.log"
    _description = "Imin HR Webhook Log"

    name = fields.Char('User Name')
    department = fields.Char('Department')
    device_name = fields.Char('Device Name')
    device_sn = fields.Char('Device SN')
    has_mask = fields.Char('Has Mask')
    md_code = fields.Char('Md Code')
    member_id = fields.Char('Member ID')
    recognize_mode = fields.Char('Recognize Mode')
    record_time = fields.Char('Record Time')
    status = fields.Char('Status')
    temperature = fields.Char('Temperature')
    state = fields.Selection([
        ('failed', 'Failed'),
        ('success', 'Success')
    ], string='State')
