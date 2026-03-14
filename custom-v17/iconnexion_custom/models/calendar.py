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