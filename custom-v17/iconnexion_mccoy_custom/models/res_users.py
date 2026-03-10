# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class ResUsers(models.Model):
    _inherit = 'res.users'


    cs_invoice_sequence_type = fields.Selection([
        ('invoice taiwan', 'INT'),
        ('invoice india', 'INI'),
    ], string='Invoice Sequence Type')