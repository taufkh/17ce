# -*- coding: utf-8 -*-
from odoo import api, fields, models

class Page(models.Model):
    _inherit = 'website.page'

    mailing_list_id = fields.Many2one('mailing.list', string='Mailing Lists')
    user_id = fields.Many2one('res.users', string='Salesperson', index=True)
    team_id = fields.Many2one('crm.team', string='Sales Team', index=True, readonly=False)

class MailingContact(models.Model):
    _inherit = 'mailing.contact'

    preferred_date_to_call = fields.Date(string='Preferred Date')
    preferred_time_to_call = fields.Selection([
        ('9am_to_12pm', '09.00AM to 12.00PM'), 
        ('12pm_to_3pm', '12.00PM to 03.00PM'), 
        ('3pm_to_6pm', '03.00PM to 06.00PM')],
        string='Preferred Time' )

    
