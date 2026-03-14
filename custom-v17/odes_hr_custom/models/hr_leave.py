# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import math

from collections import namedtuple

from datetime import datetime, date, timedelta, time
from dateutil.rrule import rrule, DAILY
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'


    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        for values in vals_list:
            holiday_status_id = values.get('holiday_status_id', False)
            employee_id = values.get('employee_id', False)
            request_date_from = values.get('request_date_from', False)

            if holiday_status_id and employee_id:
                leave_type = self.env['hr.leave.type'].sudo().search([('id','=',holiday_status_id)], limit=1)
                employee = self.env['hr.employee'].sudo().search([('id','=',employee_id)], limit=1)

                if leave_type and employee and request_date_from:
                    request_date_from = datetime.strptime(request_date_from, '%Y-%m-%d').date()
                    day_differences = (request_date_from - employee.join_date).days

                    if 'Maternity Leave' in leave_type.display_name and day_differences < 90:
                        raise AccessError(_('You need to work minimum 3 months for Maternity Leaves'))

                    if 'Childcare Leave' in leave_type.display_name:
                        if day_differences < 90:
                            raise AccessError(_('You need to work minimum 3 months for Childcare Leaves'))

                        else:
                            dependents = self.env['dependents'].sudo().search([('employee_id','=',employee_id)], order='birth_date desc', limit=1)
                            for dependent in dependents:
                                dependent_birth_date = dependent.birth_date
                                today = date.today()

                                dependent_age = today.year - dependent_birth_date.year - ((today.month, today.day) < (dependent_birth_date.month, dependent_birth_date.day))

                                if dependent_age >= 7:
                                    raise AccessError(_('Youngest child must below 7 years old for Childcare Leaves'))

        holidays = super(HolidaysRequest, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

        return holidays
