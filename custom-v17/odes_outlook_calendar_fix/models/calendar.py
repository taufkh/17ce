import pytz
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

ATTENDEE_CONVERTER_M2O = {
    'notResponded': 'needsAction',
    'tentativelyAccepted': 'tentative',
    'declined': 'declined',
    'accepted': 'accepted',
    'organizer': 'accepted',
}
MAX_RECURRENT_EVENT = 10

class Meeting(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def _get_microsoft_synced_fields(self):
        # print('_get_microsoft_synced_fields-')
        return {'name', 'description', 'allday', 'start', 'date_end', 'stop',
                'user_id', 'privacy',
                'attendee_ids', 'alarm_ids', 'location', 'show_as', 'active','teams_link'}

    @api.model
    def _microsoft_to_odoo_values(self, microsoft_event, default_reminders=(), default_values={}):
        # print('_microsoft_to_odoo_values-CUSTOM')
        if microsoft_event.is_cancelled():
            return {'active': False}

        sensitivity_o2m = {
            'normal': 'public',
            'private': 'private',
            'confidential': 'confidential',
        }

        commands_attendee, commands_partner = self._odoo_attendee_commands_m(microsoft_event)
        timeZone_start = pytz.timezone(microsoft_event.start.get('timeZone'))
        timeZone_stop = pytz.timezone(microsoft_event.end.get('timeZone'))
        start = parse(microsoft_event.start.get('dateTime')).astimezone(timeZone_start).replace(tzinfo=None)
        if microsoft_event.isAllDay:
            stop = parse(microsoft_event.end.get('dateTime')).astimezone(timeZone_stop).replace(tzinfo=None) - relativedelta(days=1)
        else:
            stop = parse(microsoft_event.end.get('dateTime')).astimezone(timeZone_stop).replace(tzinfo=None)
        values = {
            **default_values,
            'name': microsoft_event.subject or _("(No title)"),
            'description': microsoft_event.bodyPreview,
            'location': microsoft_event.location and microsoft_event.location.get('displayName') or False,
            'user_id': microsoft_event.owner(self.env).id,
            'privacy': sensitivity_o2m.get(microsoft_event.sensitivity, self.default_get(['privacy'])['privacy']),
            'attendee_ids': commands_attendee,
            'partner_ids': commands_partner,
            'allday': microsoft_event.isAllDay,
            'start': start,
            'stop': stop,
            'show_as': 'free' if microsoft_event.showAs == 'free' else 'busy',
            'recurrency': microsoft_event.is_recurrent()
        }
        if microsoft_event.onlineMeeting:
            # print(microsoft_event.onlineMeeting['joinUrl'])
            values['teams_link'] = microsoft_event.onlineMeeting['joinUrl']

        values['microsoft_id'] = microsoft_event.id
        if microsoft_event.is_recurrent():
            values['microsoft_recurrence_master_id'] = microsoft_event.seriesMasterId

        alarm_commands = self._odoo_reminders_commands_m(microsoft_event)
        if alarm_commands:
            values['alarm_ids'] = alarm_commands

        return values


    @api.model
    def _odoo_attendee_commands_m(self, microsoft_event):
        # print('_odoo_attendee_commands_m-CUSTOM')
        # return False
        commands_attendee = []
        commands_partner = []

        microsoft_attendees = microsoft_event.attendees or []
        if microsoft_event.isOrganizer:
            user = microsoft_event.owner(self.env)
            microsoft_attendees += [{
                'emailAddress': {'address': user.partner_id.email},
                'status': {'response': 'organizer'}
            }]
        emails = [a.get('emailAddress').get('address') for a in microsoft_attendees]
        existing_attendees = self.env['calendar.attendee']
        if microsoft_event.exists(self.env):
            existing_attendees = self.env['calendar.attendee'].search([
                ('event_id', '=', microsoft_event.odoo_id(self.env)),
                ('email', 'in', emails)])
        attendees_by_emails = {a.email: a for a in existing_attendees}
        for attendee in microsoft_attendees:
            email = attendee.get('emailAddress').get('address')
            state = ATTENDEE_CONVERTER_M2O.get(attendee.get('status').get('response'))

            if email in attendees_by_emails:
                # Update existing attendees
                commands_attendee += [(1, attendees_by_emails[email].id, {'state': state})]
            else:
                # Create new attendees
                if email:
                    partner = self.env['res.partner'].find_or_create(email)
                    commands_attendee += [(0, 0, {'state': state, 'partner_id': partner.id})]
                    commands_partner += [(4, partner.id)]
                    if attendee.get('emailAddress').get('name') and not partner.name:
                        partner.name = attendee.get('emailAddress').get('name')
        for odoo_attendee in attendees_by_emails.values():
            # Remove old attendees
            if odoo_attendee.email not in emails:
                commands_attendee += [(2, odoo_attendee.id)]
                commands_partner += [(3, odoo_attendee.partner_id.id)]
        return commands_attendee, commands_partner

    def _microsoft_values(self, fields_to_sync, initial_values={}):
        values = dict(initial_values)
        if not fields_to_sync:
            return values
        values['id'] = self.microsoft_id
        microsoft_guid = self.env['ir.config_parameter'].sudo().get_param('microsoft_calendar.microsoft_guid', False)
        values['singleValueExtendedProperties'] = [{
            'id': 'String {%s} Name odoo_id' % microsoft_guid,
            'value': str(self.id),
        }, {
            'id': 'String {%s} Name owner_odoo_id' % microsoft_guid,
            'value': str(self.user_id.id),
        }]

        if self.microsoft_recurrence_master_id and 'type' not in values:
            values['seriesMasterId'] = self.microsoft_recurrence_master_id
            values['type'] = 'exception'

        if 'name' in fields_to_sync:
            values['subject'] = self.name or ''

        if 'description' in fields_to_sync:
            values['body'] = {
                'content': self.description or '',
                'contentType': "text",
            }

        if any(x in fields_to_sync for x in ['allday', 'start', 'date_end', 'stop']):
            if self.allday:
                start = {'dateTime': self.start_date.isoformat(), 'timeZone': 'Europe/London'}
                end = {'dateTime': (self.stop_date + relativedelta(days=1)).isoformat(), 'timeZone': 'Europe/London'}
            else:
                start = {'dateTime': pytz.utc.localize(self.start).isoformat(), 'timeZone': 'Europe/London'}
                end = {'dateTime': pytz.utc.localize(self.stop).isoformat(), 'timeZone': 'Europe/London'}

            values['start'] = start
            values['end'] = end
            values['isAllDay'] = self.allday

        if 'location' in fields_to_sync:
            values['location'] = {'displayName': self.location or ''}

        if 'alarm_ids' in fields_to_sync:
            alarm_id = self.alarm_ids.filtered(lambda a: a.alarm_type == 'notification')[:1]
            values['isReminderOn'] = bool(alarm_id)
            values['reminderMinutesBeforeStart'] = alarm_id.duration_minutes

        if 'user_id' in fields_to_sync:
            values['organizer'] = {'emailAddress': {'address': self.user_id.email or '', 'name': self.user_id.display_name or ''}}
            values['isOrganizer'] = self.user_id == self.env.user

        if 'attendee_ids' in fields_to_sync:
            attendees = self.attendee_ids.filtered(lambda att: att.partner_id not in self.user_id.partner_id)
            values['attendees'] = [
                {
                    'emailAddress': {'address': attendee.email or '', 'name': attendee.display_name or ''},
                    'status': {'response': self._get_attendee_status_o2m(attendee)}
                } for attendee in attendees]

        if 'privacy' in fields_to_sync or 'show_as' in fields_to_sync:
            values['showAs'] = self.show_as
            sensitivity_o2m = {
                'public': 'normal',
                'private': 'private',
                'confidential': 'confidential',
            }
            values['sensitivity'] = sensitivity_o2m.get(self.privacy)

        if 'active' in fields_to_sync and not self.active:
            values['isCancelled'] = True

        if 'teams_link' in fields_to_sync:
            # values['onlineMeetingUrl'] = self.teams_link
            if self.teams_link:
                values['isOnlineMeeting'] = True

        if values.get('type') == 'seriesMaster':
            recurrence = self.recurrence_id
            pattern = {
                'interval': recurrence.interval
            }
            if recurrence.rrule_type in ['daily', 'weekly']:
                pattern['type'] = recurrence.rrule_type
            else:
                prefix = 'absolute' if recurrence.month_by == 'date' else 'relative'
                pattern['type'] = prefix + recurrence.rrule_type.capitalize()

            if recurrence.month_by == 'date':
                pattern['dayOfMonth'] = recurrence.day

            if recurrence.month_by == 'day' or recurrence.rrule_type == 'weekly':
                pattern['daysOfWeek'] = [
                    weekday_name for weekday_name, weekday in {
                        'monday': recurrence.mo,
                        'tuesday': recurrence.tu,
                        'wednesday': recurrence.we,
                        'thursday': recurrence.th,
                        'friday': recurrence.fr,
                        'saturday': recurrence.sa,
                        'sunday': recurrence.su,
                    }.items() if weekday]
                pattern['firstDayOfWeek'] = 'sunday'

            if recurrence.rrule_type == 'monthly' and recurrence.month_by == 'day':
                byday_selection = [
                    ('1', 'first'),
                    ('2', 'second'),
                    ('3', 'third'),
                    ('4', 'fourth'),
                    ('-1', 'last')
                ]
                pattern['index'] = byday_selection[recurrence.byday]

            rule_range = {
                'startDate': (recurrence.dtstart.date()).isoformat()
            }

            if recurrence.end_type == 'count':  # e.g. stop after X occurence
                rule_range['numberOfOccurrences'] = min(recurrence.count, MAX_RECURRENT_EVENT)
                rule_range['type'] = 'numbered'
            elif recurrence.end_type == 'forever':
                rule_range['numberOfOccurrences'] = MAX_RECURRENT_EVENT
                rule_range['type'] = 'numbered'
            elif recurrence.end_type == 'end_date':  # e.g. stop after 12/10/2020
                rule_range['endDate'] = recurrence.until.isoformat()
                rule_range['type'] = 'endDate'

            values['recurrence'] = {
                'pattern': pattern,
                'range': rule_range
            }
        # print(values,'_microsoft_values--CUSTOM')

        return values