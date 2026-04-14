# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class CalendarEvent(models.Model):
	_inherit = "calendar.event"

	is_visit = fields.Boolean('Visit')
	visit_type = fields.Selection([('physical','Physical'),('virtual','Virtual')],string="Visit Type")
	customer_id = fields.Many2one('res.partner', string='Customer')
	internal_user_ids = fields.Many2many('res.users', string='Internal Attendees')
	meeting_agenda = fields.Text('Agenda')
	next_followup_plan = fields.Text('Next Follow-up Plan')
	action_item_ids = fields.One2many('calendar.event.visit.action', 'event_id', string='Action Items')

	@api.onchange('opportunity_id')
	def _onchange_opportunity_id_visit_defaults(self):
		for event in self:
			if event.opportunity_id and not event.customer_id:
				event.customer_id = event.opportunity_id.partner_id.commercial_partner_id


class CalendarEventVisitAction(models.Model):
	_name = 'calendar.event.visit.action'
	_description = 'Customer Visit Action Item'
	_order = 'sequence, id'

	sequence = fields.Integer(default=10)
	event_id = fields.Many2one('calendar.event', string='Meeting', required=True, ondelete='cascade')
	name = fields.Char(string='Action Item', required=True)
	owner_id = fields.Many2one('res.users', string='Owner')
	due_date = fields.Date(string='Due Date')
	is_done = fields.Boolean(string='Done')
	note = fields.Text(string='Notes')
