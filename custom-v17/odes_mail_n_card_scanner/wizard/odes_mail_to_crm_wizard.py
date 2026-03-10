
from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class OdesMailToCRMWizard(models.TransientModel):
    _name = "odes.mail.to.crm.wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "ODES Mail To CRM Wizard"

    name = fields.Char("Subject")
    message = fields.Text("Message")
    is_create_crm = fields.Boolean("Create CRM")

    def fetch_mail(self,fectmail):
        country_obj = self.env['res.country']
        crm_obj = self.env['crm.lead']
        for r in self:
            r.write({'is_create_crm':True})
            for message in r.message_ids:
                email_from = message.email_from
                email_from = email_from[:-1].split('.')
                email_from = email_from[len(email_from)-1]
                country_code = email_from.upper()
                dict_data = {
                    'name':message.subject or 'New Message From Email',
                    'email_from':message.email_from,
                    'source':'website_email',
                }
                
                if fectmail.default_salesperson_id:
                    dict_data['user_id'] = fectmail.default_salesperson_id.id
                if fectmail.default_salesteam_id:
                    dict_data['team_id'] = fectmail.default_salesteam_id.id
                if fectmail.default_country_id:
                    dict_data['country_id'] = fectmail.default_country_id.id
                if fectmail.default_company_id:
                    dict_data['company_id'] = fectmail.default_company_id.id
                partner_id = fectmail.default_salesperson_id.partner_id.id
                try:
                    crm = crm_obj.sudo().with_context(notify_by_email=True,mail_notify_force_send=True,force_send=True,odes_incoming_mail_crm_partner=partner_id,odes_incoming_mail_crm_email=fectmail.default_salesperson_id.partner_id.email).create(dict_data)
                    message.write({"model":'crm.lead','res_id':crm.id})
                    crm.write({'website_message_ids':[(4, message.id)],'message_ids':[(4, message.id)]})
                except:
                    continue
        return True
