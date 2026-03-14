import calendar
from datetime import datetime, time, timedelta

import pytz

from odoo import fields, models


class CalendarAppointmentAnswer(models.Model):
    _name = 'calendar.appointment.answer'
    _description = 'Appointment Answer'

    name = fields.Char(required=True)
    question_id = fields.Many2one('calendar.appointment.question', required=True, ondelete='cascade')


class CalendarAppointmentQuestion(models.Model):
    _name = 'calendar.appointment.question'
    _description = 'Appointment Question'

    name = fields.Char(required=True)
    appointment_type_id = fields.Many2one('calendar.appointment.type', required=True, ondelete='cascade')
    question_type = fields.Selection(
        [('char', 'Text'), ('text', 'Long Text'), ('select', 'Select'), ('radio', 'Radio'), ('checkbox', 'Checkbox')],
        default='char',
    )
    question_required = fields.Boolean()
    placeholder = fields.Char()
    answer_ids = fields.One2many('calendar.appointment.answer', 'question_id')


class CalendarAppointmentType(models.Model):
    _name = 'calendar.appointment.type'
    _description = 'Appointment Type'

    name = fields.Char(required=True)
    appointment_tz = fields.Char(default=lambda self: self.env.user.tz or 'UTC')
    appointment_duration = fields.Float(default=1.0)
    assignation_method = fields.Selection([('chosen', 'Chosen'), ('random', 'Random')], default='chosen')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    country_ids = fields.Many2many('res.country', string='Countries')
    message_intro = fields.Html()
    message_confirmation = fields.Html()
    reminder_ids = fields.Many2many('calendar.alarm', string='Reminders')
    location = fields.Char()
    min_cancellation_hours = fields.Integer(default=0)
    question_ids = fields.One2many('calendar.appointment.question', 'appointment_type_id')
    website_url = fields.Char(compute='_compute_website_url')

    def _compute_website_url(self):
        for appointment in self:
            appointment.website_url = '/appointment/%s' % appointment.id

    def _get_appointment_slots(self, timezone_name, employee=False):
        self.ensure_one()
        tz = pytz.timezone(timezone_name or self.appointment_tz or 'UTC')
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        now_local = now_utc.astimezone(tz)
        start_day = now_local.date()
        end_day = start_day + timedelta(days=28)
        duration_minutes = max(15, int((self.appointment_duration or 1.0) * 60))

        calendar_rows = {}
        iter_day = start_day
        while iter_day <= end_day:
            month_key = iter_day.replace(day=1)
            if month_key not in calendar_rows:
                calendar_rows[month_key] = {}
            slots = self._day_slots(iter_day, tz, duration_minutes, employee)
            calendar_rows[month_key][iter_day] = slots
            iter_day += timedelta(days=1)

        result = []
        for month_start, day_map in sorted(calendar_rows.items(), key=lambda item: item[0]):
            cal = calendar.Calendar(firstweekday=0)
            weeks = []
            for week in cal.monthdatescalendar(month_start.year, month_start.month):
                week_days = []
                for week_day in week:
                    in_month = week_day.month == month_start.month
                    day_slots = day_map.get(week_day, []) if in_month else []
                    week_days.append({
                        'day': week_day,
                        'slots': day_slots,
                        'weekend_cls': 'text-muted' if week_day.weekday() >= 5 else '',
                        'today_cls': 'o_website_calendar_today' if week_day == start_day else '',
                        'mute_cls': 'text-muted' if not in_month else '',
                    })
                weeks.append(week_days)
            result.append({
                'month': month_start.strftime('%B %Y'),
                'weeks': weeks,
            })
        return result

    def _day_slots(self, slot_date, tz, duration_minutes, employee=False):
        # Business hour slots: 09:00-17:00 local timezone, filtered by availability.
        slots = []
        start_hour = 9
        end_hour = 17
        employee_partner = False
        if employee and employee.user_id:
            employee_partner = employee.user_id.partner_id

        slot_start_local = datetime.combine(slot_date, time(hour=start_hour, minute=0))
        last_slot_local = datetime.combine(slot_date, time(hour=end_hour, minute=0))
        while slot_start_local < last_slot_local:
            slot_end_local = slot_start_local + timedelta(minutes=duration_minutes)
            if slot_end_local > last_slot_local:
                break
            slot_start_utc = tz.localize(slot_start_local).astimezone(pytz.utc).replace(tzinfo=None)
            slot_end_utc = tz.localize(slot_end_local).astimezone(pytz.utc).replace(tzinfo=None)

            if slot_start_utc > fields.Datetime.now():
                if self._is_slot_available(slot_start_utc, slot_end_utc, employee_partner):
                    slots.append({
                        'employee_id': employee.id if employee else False,
                        'datetime': fields.Datetime.to_string(slot_start_utc),
                        'hours': slot_start_local.strftime('%H:%M'),
                    })
            slot_start_local += timedelta(minutes=duration_minutes)
        return slots

    def _is_slot_available(self, start_dt, end_dt, employee_partner=False):
        if employee_partner and not employee_partner.calendar_verify_availability(start_dt, end_dt):
            return False
        conflict_domain = [
            ('appointment_type_id', '=', self.id),
            ('start', '<', fields.Datetime.to_string(end_dt)),
            ('stop', '>', fields.Datetime.to_string(start_dt)),
        ]
        return not bool(self.env['calendar.event'].sudo().search_count(conflict_domain))


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    appointment_type_id = fields.Many2one('calendar.appointment.type')
