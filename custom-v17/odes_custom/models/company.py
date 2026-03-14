# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class ResCompany(models.Model):
    _inherit = "res.company"

    is_project = fields.Boolean('Auto Create Project', default=False)
    is_odes = fields.Boolean('ODES Company', default=False)
    is_mccoy = fields.Boolean('McCoy Company', default=False)

    crm_stage_ids = fields.Many2many('crm.stage', 'company_crm_stage_rel', 'company_id', 'stage_id', string='CRM Stages')
    email_cc = fields.Char('Email CC') ###NOT USED
    is_sf = fields.Boolean('Sales Figure', default=False) ###NOT USED

    company_code = fields.Char('Company Code')

    odes_currency_ids = fields.Many2many('res.currency', string='Available Currencies',)