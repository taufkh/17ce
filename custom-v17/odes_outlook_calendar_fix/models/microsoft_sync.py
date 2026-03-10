# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from contextlib import contextmanager
from functools import wraps
import requests
import pytz
from dateutil.parser import parse

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, registry, _
from odoo.tools import ormcache_context
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.addons.microsoft_calendar.models.microsoft_sync import microsoft_calendar_token

from odoo.addons.microsoft_calendar.utils.microsoft_event import MicrosoftEvent
from odoo.addons.microsoft_calendar.utils.microsoft_calendar import MicrosoftCalendarService,InvalidSyncToken
from odoo.addons.microsoft_account.models.microsoft_service import TIMEOUT
import datetime
from datetime import datetime, timedelta

MAX_RECURRENT_EVENT = 10

class MicrosoftSync(models.AbstractModel):
    _inherit = 'microsoft.calendar.sync'

    @api.model_create_multi
    def create(self, vals_list):
        # if any(vals.get('microsoft_id') for vals in vals_list):
        #     self._from_microsoft_ids.clear_cache(self)
        if vals_list and type(vals_list) == list:
            if 'rrule_type' in vals_list[0] and 'calendar_event_ids' in vals_list[0]:
                for cal in vals_list[0]['calendar_event_ids'][:]:
                    if len(cal) > 2:
                        if 'start' in cal[2]:
                            start = cal[2]['start']
                            start = start.strftime('%Y-%m-%d')
                            start = datetime.strptime(start,('%Y-%m-%d'))
                            today = datetime.now().strftime('%Y-%m-%d')
                            today = datetime.strptime(today,('%Y-%m-%d'))
                            if not (start > today and start < today + relativedelta(days=14)):
                                vals_list[0]['calendar_event_ids'].remove(cal)

        
        if 'rrule_type' not in str(vals_list):
            if 'start' in str(vals_list) or 'stop' in str(vals_list):
                if vals_list[0]['start'] == None or vals_list[0]['stop'] == None:
                    vals_list = []
        # records = super().create(vals_list)
        records = super(MicrosoftSync, self).create(vals_list)
        # microsoft_service = MicrosoftCalendarService(self.env['microsoft.service'])
        # records_to_sync = records.filtered(lambda r: r.need_sync_m and r.active)
        # for record in records_to_sync:
        #     record._microsoft_insert(microsoft_service, record._microsoft_values(self._get_microsoft_synced_fields()), timeout=3)
        return records


    def _sync_odoo2microsoft(self, microsoft_service: MicrosoftCalendarService):
        # print(self, '_sync_odoo2microsoft-CUSTOM')
        alarm_ids = self.env['calendar.event'].search([('alarm_ids','!=',False),('active','=',True)])
        if alarm_ids:
            for al in alarm_ids:
                today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                today = datetime.strptime(today,('%Y-%m-%d %H:%M:%S')) + timedelta(hours=8)
                today_date = datetime.now().strftime('%Y-%m-%d')
                if al.start:
                    start = al.start + timedelta(hours=8)
                    if start < today:
                        if al.alarm_ids:
                            al.write({'alarm_ids':False})

                if al.start_date:
                    start_date = al.start_date
                    start_date = start_date.strftime('%Y-%m-%d')
                    if start_date < today_date:
                        if al.alarm_ids:
                            al.write({'alarm_ids': False})
                
        if not self:
            return
        if self._active_name:
            records_to_sync = self.filtered(self._active_name)
        else:
            records_to_sync = self
        cancelled_records = self - records_to_sync
        
        updated_records = records_to_sync.filtered('microsoft_id')
        new_records = records_to_sync - updated_records
        
        for record in cancelled_records.filtered('microsoft_id'):
            record._microsoft_delete(microsoft_service, record.microsoft_id)
        for record in new_records:
            values = record._microsoft_values(self._get_microsoft_synced_fields())
            if 'start' in str(values):
                if type(values) == dict:
                    if values['start']:
                        if values['start']['dateTime']:
                            start = values['start']['dateTime']
                            today = datetime.now().strftime('%Y-%m-%d')
                            if start < today:
                                continue

                # if type(values) == list:
                #     if values[0]['start']:
                #         if values[0]['start']['dateTime']:
                #             start = values[0]['start']['dateTime']
                #             today = datetime.now().strftime('%Y-%m-%d')
                #             if start < today:
                #                 continue
            if isinstance(values, dict):
                record._microsoft_insert(microsoft_service, values)
            else:
                for value in values:
                    record._microsoft_insert(microsoft_service, value)

        for record in updated_records:
            values = record._microsoft_values(self._get_microsoft_synced_fields())
            if 'start' in str(values):
                if type(values) == dict:
                    if values['start']:
                        if values['start']['dateTime']:
                            start = values['start']['dateTime']
                            today = datetime.now().strftime('%Y-%m-%d')
                            if start < today:
                                continue

                # if type(values) == list:
                #     if values[0]['start']:
                #         if values[0]['start']['dateTime']:
                #             start = values[0]['start']['dateTime']
                #             today = datetime.now().strftime('%Y-%m-%d')
                #             if start < today:
                #                 continue
            if not values:
                continue
            record._microsoft_patch(microsoft_service, record.microsoft_id, values)

    @api.model
    def _sync_microsoft2odoo(self, microsoft_events: MicrosoftEvent, default_reminders=()):
        # print(self,'_sync_microsoft2odoo CUSTOM---------')
        """Synchronize Microsoft recurrences in Odoo. Creates new recurrences, updates
        existing ones.

        :return: synchronized odoo
        """
        if microsoft_events:
            existing = microsoft_events.exists(self.env)
            new = microsoft_events - existing - microsoft_events.cancelled()
            new_recurrent = new.filter(lambda e: e.is_recurrent())

            default_values = {}

            odoo_values = [
                dict(self._microsoft_to_odoo_values(e, default_reminders, default_values), need_sync_m=False)
                for e in (new - new_recurrent)
            ]
            # print(odoo_values,'ODOO VALUES-AWAL+++',len(odoo_values))
            for values in odoo_values[:]:
                if 'start' in str(values):
                    if values['start']:
                        start = values['start']
                        start = start.strftime('%Y-%m-%d')
                        start = datetime.strptime(start,('%Y-%m-%d'))
                        today = datetime.now().strftime('%Y-%m-%d')
                        today = datetime.strptime(today,('%Y-%m-%d'))
                        # print(today,start,'TODAY -- START',type(today),type(start))
                        starts = values['start']
                        start_date = values['start']
                        starts = starts.strftime('%Y-%m-%d %H:%M:%S')
                        start_date = start_date.strftime('%Y-%m-%d')
                        duplicate_ids = self.env['calendar.event'].search([('name','=',values['name']),('start','=',starts)])
                        duplicate2_ids = self.env['calendar.event'].search([('name','=',values['name']),('start_date','=',start_date)])

                        if start < today or duplicate_ids or duplicate2_ids:
                            # print('Lebih Kecil--')
                            odoo_values.remove(values)
                            # new_odoo = False or ()
                            # continue
            # print(odoo_values,'ODOO VALUES-AKHIR+++',len(odoo_values))
            new_odoo = self.create(odoo_values)
            synced_recurrent_records = self._sync_recurrence_microsoft2odoo(new_recurrent)
            cancelled = existing.cancelled()
            cancelled_odoo = self.browse(cancelled.odoo_ids(self.env))
            if cancelled_odoo:
                for cancel in cancelled_odoo:
                    cancel_odoo = self.env['calendar.event'].search([('id','=',cancel.id)])
                    if not cancel_odoo:
                        continue
                    cancel_odoo._cancel_microsoft()

            recurrent_cancelled = self.env['calendar.recurrence'].search([
                ('microsoft_id', 'in', (microsoft_events.cancelled() - cancelled).microsoft_ids())])
            recurrent_cancelled._cancel_microsoft()

            synced_records = new_odoo + cancelled_odoo + synced_recurrent_records.calendar_event_ids
            for mevent in (existing - cancelled).filter(lambda e: e.lastModifiedDateTime and not e.seriesMasterId):
                # Last updated wins.
                # This could be dangerous if microsoft server time and odoo server time are different
                if mevent.is_recurrence():
                    odoo_record = self.env['calendar.recurrence'].browse(mevent.odoo_id(self.env))
                else:
                    odoo_record = self.browse(mevent.odoo_id(self.env))
                odoo_record_updated = pytz.utc.localize(odoo_record.write_date)
                updated = parse(mevent.lastModifiedDateTime or str(odoo_record_updated))
                if updated >= odoo_record_updated:
                    vals = dict(odoo_record._microsoft_to_odoo_values(mevent, default_reminders), need_sync_m=False)
                    odoo_record.write(vals)
                    if odoo_record._name == 'calendar.recurrence':
                        odoo_record._update_microsoft_recurrence(mevent, microsoft_events)
                        synced_recurrent_records |= odoo_record
                    else:
                        synced_records |= odoo_record

            return synced_records, synced_recurrent_records


    def _sync_recurrence_microsoft2odoo(self, microsoft_events: MicrosoftEvent):
        # print('_sync_recurrence_microsoft2odoo-CUSTOM -',MAX_RECURRENT_EVENT)
        recurrent_masters = microsoft_events.filter(lambda e: e.is_recurrence())
        recurrents = microsoft_events.filter(lambda e: e.is_recurrent_not_master())
        default_values = {'need_sync_m': False}

        new_recurrence = self.env['calendar.recurrence']

        for recurrent_master in recurrent_masters:
            new_calendar_recurrence = dict(self.env['calendar.recurrence']._microsoft_to_odoo_values(recurrent_master, (), default_values), need_sync_m=False)
            to_create = recurrents.filter(lambda e: e.seriesMasterId == new_calendar_recurrence['microsoft_id'])
            recurrents -= to_create
            base_values = dict(self.env['calendar.event']._microsoft_to_odoo_values(recurrent_master, (), default_values), need_sync_m=False)
            to_create_values = []
            if new_calendar_recurrence.get('end_type', False) in ['count', 'forever']:
                to_create = list(to_create)[:MAX_RECURRENT_EVENT]
            for recurrent_event in to_create:
                if recurrent_event.type == 'occurrence':
                    value = self.env['calendar.event']._microsoft_to_odoo_recurrence_values(recurrent_event, (), base_values)
                else:
                    value = self.env['calendar.event']._microsoft_to_odoo_values(recurrent_event, (), default_values)

                to_create_values += [dict(value, need_sync_m=False)]

            new_calendar_recurrence['calendar_event_ids'] = [(0, 0, to_create_value) for to_create_value in to_create_values]
            new_recurrence_odoo = self.env['calendar.recurrence'].create(new_calendar_recurrence)
            new_recurrence_odoo.base_event_id = new_recurrence_odoo.calendar_event_ids[0] if new_recurrence_odoo.calendar_event_ids else False
            new_recurrence |= new_recurrence_odoo

        for recurrent_master_id in set([x.seriesMasterId for x in recurrents]):
            recurrence_id = self.env['calendar.recurrence'].search([('microsoft_id', '=', recurrent_master_id)])
            to_update = recurrents.filter(lambda e: e.seriesMasterId == recurrent_master_id)
            for recurrent_event in to_update:
                if recurrent_event.type == 'occurrence':
                    value = self.env['calendar.event']._microsoft_to_odoo_recurrence_values(recurrent_event, (), {'need_sync_m': False})
                else:
                    value = self.env['calendar.event']._microsoft_to_odoo_values(recurrent_event, (), default_values)
                existing_event = recurrence_id.calendar_event_ids.filtered(lambda e: e._range() == (value['start'], value['stop']))
                if not existing_event:
                    continue
                value.pop('start')
                value.pop('stop')
                existing_event.write(value)
            new_recurrence |= recurrence_id
        return new_recurrence

    def _update_microsoft_recurrence(self, recurrence_event, events):
        # print('_update_microsoft_recurrence-CUSTOM-',MAX_RECURRENT_EVENT)
        vals = dict(self.base_event_id._microsoft_to_odoo_values(recurrence_event, ()), need_sync_m=False)
        vals['microsoft_recurrence_master_id'] = vals.pop('microsoft_id')
        self.base_event_id.write(vals)
        values = {}
        default_values = {}

        normal_events = []
        events_to_update = events.filter(lambda e: e.seriesMasterId == self.microsoft_id)
        if self.end_type in ['count', 'forever']:
            events_to_update = list(events_to_update)[:MAX_RECURRENT_EVENT]

        for recurrent_event in events_to_update:
            if recurrent_event.type == 'occurrence':
                value = self.env['calendar.event']._microsoft_to_odoo_recurrence_values(recurrent_event, (), default_values)
                normal_events += [recurrent_event.odoo_id(self.env)]
            else:
                value = self.env['calendar.event']._microsoft_to_odoo_values(recurrent_event, (), default_values)
                self.env['calendar.event'].browse(recurrent_event.odoo_id(self.env)).with_context(no_mail_to_attendees=True, mail_create_nolog=True).write(dict(value, need_sync_m=False))
            values[(self.id, value.get('start'), value.get('stop'))] = dict(value, need_sync_m=False)

        if (self.id, vals.get('start'), vals.get('stop')) in values:
            base_event_vals = dict(vals)
            base_event_vals.update(values[(self.id, vals.get('start'), vals.get('stop'))])
            self.base_event_id.write(base_event_vals)

        old_record = self._apply_recurrence(specific_values_creation=values, no_send_edit=True)

        vals.pop('microsoft_id', None)
        vals.pop('start', None)
        vals.pop('stop', None)
        normal_events = [e for e in normal_events if e in self.calendar_event_ids.ids]
        normal_event_ids = self.env['calendar.event'].browse(normal_events) - old_record
        if normal_event_ids:
            vals['follow_recurrence'] = True
            (self.env['calendar.event'].browse(normal_events) - old_record).write(vals)

        old_record._cancel_microsoft()
        if not self.base_event_id:
            self.base_event_id = self._get_first_event(include_outliers=False)

# class User(models.Model):
#     _inherit = 'res.users'

#     report_user_id = fields.Many2one('res.users','Users')
#     report_to_user_ids = fields.Many2one('res.users','Users1')
#     report_to_user_crm_ids = fields.Many2one('res.users','Users2')
#     is_select_company = fields.Boolean('Select Company')
    # def _sync_microsoft_calendar(self, calendar_service: MicrosoftCalendarService):
    #     # print('_sync_microsoft_calendar CUSTOM---------')
    #     self.ensure_one()
    #     full_sync = not bool(self.microsoft_calendar_sync_token)
    #     with microsoft_calendar_token(self) as token:
    #         try:
    #             events, next_sync_token, default_reminders = calendar_service.get_events(self.microsoft_calendar_sync_token, token=token)
    #         except InvalidSyncToken:
    #             events, next_sync_token, default_reminders = calendar_service.get_events(token=token)
    #             full_sync = True
    #     self.microsoft_calendar_sync_token = next_sync_token
    #     # Microsoft -> Odoo
    #     recurrences = events.filter(lambda e: e.is_recurrent())
    #     try:
    #         synced_events, synced_recurrences = self.env['calendar.event']._sync_microsoft2odoo(events, default_reminders=default_reminders) if events else (self.env['calendar.event'], self.env['calendar.recurrence'])
    #     except:
    #         return 0,0
    #     # Odoo -> Microsoft
    #     recurrences = self.env['calendar.recurrence']._get_microsoft_records_to_sync(full_sync=full_sync)
    #     recurrences -= synced_recurrences
    #     recurrences._sync_odoo2microsoft(calendar_service)
    #     synced_events |= recurrences.calendar_event_ids

    #     events = self.env['calendar.event']._get_microsoft_records_to_sync(full_sync=full_sync)
    #     (events - synced_events)._sync_odoo2microsoft(calendar_service)

    #     return bool(events | synced_events) or bool(recurrences | synced_recurrences)