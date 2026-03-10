from datetime import timedelta
import math
import babel.dates
import logging
import pytz
import base64

from odoo import api, fields, models
from odoo import tools
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.calendar.models.calendar_attendee import Attendee
from odoo.addons.calendar.models.calendar_recurrence import weekday_to_field, RRULE_TYPE_SELECTION, END_TYPE_SELECTION, MONTH_BY_SELECTION, WEEKDAY_SELECTION, BYDAY_SELECTION
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from odoo.tools import pycompat
from odoo.exceptions import UserError, ValidationError, AccessError

class Meeting(models.Model):
    _inherit = 'calendar.event'

    teams_link = fields.Char('Microsoft Teams')
    # is_visit = fields.Boolean('Is Visit')
    # visit_type = fields.Char('Visit Type')

    def action_redirect_link(self):
        if self.teams_link:
            Url = self.teams_link
            return {'type': 'ir.actions.act_url',
                    'url': Url,
                    'target': 'new'
                    }

class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    def _send_mail_to_attendees(self, template_xmlid, force_send=False, ignore_recurrence=False):
        context = self.env.context
        """ Send mail for event invitation to event attendees.
            :param template_xmlid: xml id of the email template to use to send the invitation
            :param force_send: if set to True, the mail(s) will be sent immediately (instead of the next queue processing)
            :param ignore_recurrence: ignore event recurrence
        """
        res = False
        if self.recurrence_id or not self:
            return False
        if self.event_id:
            if not self.event_id.user_id:
                return False
        if self.env['ir.config_parameter'].sudo().get_param('calendar.block_mail') or self._context.get("no_mail_to_attendees"):
            return res

        calendar_view = self.env.ref('calendar.view_calendar_event_calendar')
        invitation_template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not invitation_template:
            _logger.warning("Template %s could not be found. %s not notified." % (template_xmlid, self))
            return
        # get ics file for all meetings
        ics_files = self.mapped('event_id')._get_ics_file()

        # prepare rendering context for mail template
        colors = {
            'needsAction': 'grey',
            'accepted': 'green',
            'tentative': '#FFFF00',
            'declined': 'red'
        }
        rendering_context = dict(self._context)
        rendering_context.update({
            'colors': colors,
            'ignore_recurrence': ignore_recurrence,
            'action_id': self.env['ir.actions.act_window'].sudo().search([('view_id', '=', calendar_view.id)], limit=1).id,
            'dbname': self._cr.dbname,
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='http://localhost:8069'),
        })

        for attendee in self:
            if attendee.email and attendee.partner_id != self.env.user.partner_id:
                # FIXME: is ics_file text or bytes?
                event_id = attendee.event_id.id
                ics_file = ics_files.get(event_id)

                attachment_values = []
                if ics_file:
                    attachment_values = [
                        (0, 0, {'name': 'invitation.ics',
                                'mimetype': 'text/calendar',
                                'datas': base64.b64encode(ics_file)})
                    ]
                body = invitation_template.with_context(rendering_context)._render_field(
                    'body_html',
                    attendee.ids,
                    compute_lang=True,
                    post_process=True)[attendee.id]
                subject = invitation_template._render_field(
                    'subject',
                    attendee.ids,
                    compute_lang=True)[attendee.id]
                attendee.event_id.with_context(no_document=True).message_notify(
                    body=body,
                    subject=subject,
                    partner_ids=attendee.partner_id.ids,
                    email_layout_xmlid='mail.mail_notification_light',
                    attachment_ids=attachment_values,
                    force_send=force_send)