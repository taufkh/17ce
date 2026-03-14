# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    opportunity_id = fields.Many2one(
        'crm.lead', 'Opportunity',
        index=True, ondelete='set null')
    minutes_record = fields.Text('Minutes Record')
    task_id = fields.Many2one(
        'project.task', 'Related Task',
        index=True, ondelete='set null')

    @api.model
    def default_get(self, fields):
        defaults = super(CalendarEvent, self).default_get(fields)

        context = dict(self._context or {})
        if not context.get('default_opportunity_id') and context.get('from_lead'):
            active_id = context.get('active_id')
            active_model = context.get('active_model')
            if active_id and active_model == 'crm.lead':
                defaults['opportunity_id'] = active_id

        return defaults

    def view_event(self):
        formview_ref = self.env.ref('calendar.view_calendar_event_form', False)
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        action['res_id'] = self.id
        action['view_mode'] = 'form'
        action['views'] = [(formview_ref and formview_ref.id or False, 'form')]
        action['target'] = 'new'

        return action
