# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class CrmStage(models.Model):
    _inherit = "crm.stage"

    is_need_so = fields.Boolean('Need SO', default=False)
    is_confirm_so = fields.Boolean('Confirm SO', default=False)
    is_revenue = fields.Boolean('Need Expected Revenue', default=False)

    company_ids = fields.Many2many('res.company', 'company_crm_stage_rel', 'stage_id', 'company_id', string='Companies')