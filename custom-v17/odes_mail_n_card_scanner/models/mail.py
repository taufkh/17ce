# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import poplib
from ssl import SSLError
from socket import gaierror, timeout
from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'


    def _notify_compute_recipients(self, message, msg_vals):
        recipient_data = super(MailThread, self)._notify_compute_recipients(message, msg_vals)
        if self._context.get('odes_incoming_mail_crm_partner'):
            cout = 0
            for p in recipient_data['partners']:
                recipient_data['partners'][cout]['notif'] = 'email'
                cout+=1
        return recipient_data

    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        result = super(MailThread, self).message_process(model, message, custom_values,
                        save_original, strip_attachments,
                        thread_id)

        return result

class FetchmailServer(models.Model):
    """Incoming POP/IMAP mail server account"""

    _inherit = 'fetchmail.server'


    default_salesperson_id = fields.Many2one("res.users","Default Salesperson")
    default_salesteam_id = fields.Many2one("crm.team","Default Salesteam")
    default_country_id = fields.Many2one("res.country","Default Country")
    default_company_id = fields.Many2one("res.company","Default Company")
    is_email_crm_country = fields.Boolean("is_email_crm_country")

    @api.model
    def default_get(self, fields):
        result = super(FetchmailServer, self).default_get(fields)
        if self._context.get('incoming_mail_crm'):
            objectset = self.env['ir.model'].search([('model','=','odes.mail.to.crm.wizard')],limit=1)
            result['object_id'] = objectset.id
        return result


    @api.onchange('object_id')
    def onchange_object_id(self):
        for rec in self:
            is_email_crm_country = False
            if rec.object_id.model == 'odes.mail.to.crm.wizard':
                is_email_crm_country = True
            rec.is_email_crm_country = is_email_crm_country


    # def fetch_mail(self):
        # w_obj = self.env['odes.mail.to.crm.wizard']
        # res = super(FetchmailServer, self).fetch_mail()
        # for data in self:
        #     if data.object_id:
        #         if data.object_id.model == 'odes.mail.to.crm.wizard':
        #             wizards = w_obj.search([('is_create_crm','=',False)])
        #             wizards.fetch_mail(data)
    #     return res

    def write(self, vals):
        w_obj = self.env['odes.mail.to.crm.wizard']
        res = super(FetchmailServer, self).write(vals)
        if vals.get('date'):
            for data in self:
                if data.object_id:
                    if data.object_id.model == 'odes.mail.to.crm.wizard':
                        wizards = w_obj.search([('is_create_crm','=',False)])
                        wizards.fetch_mail(data)

        return res



    def temporary_send_mail(self):
        self.env['crm.lead'].search([('id','in',[1088,1087])])._message_auto_subscribe_notify([10,7060],'mail.message_user_assigned')
        return True
