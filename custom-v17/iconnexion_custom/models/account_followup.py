# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from odoo.osv import expression
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta,FR,MO

class FollowupLine(models.Model):
	_inherit = 'account_followup.followup.line'


	is_weekly = fields.Boolean('Weekly Reminder', help="Automation of follow up reminders to be set to every Monday", required=False)


	def _get_next_date(self):
		self.ensure_one()
		next_followup = self.env['account_followup.followup.line'].search([('delay', '>', self.delay),
																		   ('company_id', '=', self.env.company.id)],
																		  order="delay asc", limit=1)
		if next_followup:
			delay = next_followup.delay - self.delay
		else:
			delay = 14

		if self.is_weekly:
			delay = 0
			return fields.Date.today() + relativedelta(days=delay, weekday=MO)

		return fields.Date.today() + timedelta(days=delay)

		#supaya selalu ke senin
		#values={'line': self, 'date_planned_start':(self.date_planned+ relativedelta(weeks=1, weekday=FR)).strftime('%Y-%m-%d %H:%M:%S'), 'date_planned': (date_delivery+ relativedelta(weeks=1, weekday=FR)).strftime('%Y-%m-%d %H:%M:%S')},
