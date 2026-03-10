# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.parser import parse


class OdesCrmStage(models.Model):
    _name = "odes.crm.stage"
    _description = 'ODES CRM Stage History'
    _order = 'id desc'
    _rec_name = 'lead_id'

    lead_id = fields.Many2one('crm.lead', 'CRM Lead')
    stage_id = fields.Many2one('crm.stage', 'Stage')
    stage_name = fields.Char('Stages')
    start_datetime = fields.Date('Start Time', default=fields.Datetime.now)
    end_datetime = fields.Date('End Time')
    days_count = fields.Integer(string='Days', compute="_action_count_date")
    backward_reason = fields.Char('Backward Reason')

    def _action_count_date(self):
        now = parse((datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d'))
        self.days_count = 0
        for count in self:
            day_start = count.start_datetime and parse(str(count.start_datetime)) or now
            day_end = count.end_datetime and parse(str(count.end_datetime)) or now
            
            total = (day_end - day_start).days + 1
            if count.lead_id.stage_id.is_won and not count.end_datetime:
                total = 1

            count.days_count = total


class OdesLeadStage(models.Model):
    _name = "odes.lead.stage"
    _description = "Lead Stages"

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', default=1)