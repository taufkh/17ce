import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _

from odoo.http import request
from odoo.addons.website.models import ir_http
from odoo.addons.http_routing.models.ir_http import url_for

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    odes_is_active_cookies = fields.Boolean(string='Active Cookies Notification')
    odes_button_text_cookies = fields.Char(string='Button Text', default='Accept and hide this message')
    odes_message_title_cookies = fields.Char(string='Message Title cookies', default='This website uses cookies')
    odes_message_cookies = fields.Text(string='Message cookies', default='This website uses cookies. For more information, please visit the <a target="_top" href="/cookies-policy">Privacy and Cookies Policy</a>.')


    def get_sales_teams(self):
        data = self.env['crm.team'].search([])
        return data
    
    def get_sales_teams_list(self):
#        data = self.env['crm.team.list'].search([('team_id', '='. crm.id)])
        data = self.env['crm.team.list'].search([])
        return data
    

class Team(models.Model):
    _inherit = "crm.team"

    teamList_ids = fields.One2many('crm.team.list','team_id', string='Name')
    available_in_website = fields.Boolean(string="Available In Website", default=False)

class TeamList(models.Model):
    _name = "crm.team.list"
    _description = "CRM Team List"

    name = fields.Char('Name')
    team_id = fields.Many2one('crm.team', string='Team')
        
        
class Lead(models.Model):
    _inherit = "crm.lead"
    
    list_ids = fields.Many2many('crm.team.list', 'odes_crm_team_list', string='Sub Sales Team')
#	teamList_ids = fields.One2many('crm.team.list','team_id', string='Name')
    lead_url = fields.Char(compute='_get_lead_url', string='Lead Url')

    def _get_lead_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        second_url = '/web#id='
        third_url = '&view_type=form&model=crm.lead&action='
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")

        for lead in self:
            full_url = base_url+second_url+str(lead.id)+third_url+str(action['id'])
            print (full_url, 'pppppppp')
            lead.lead_url = full_url


    def send_new_email(self):
        mail_obj = self.env['mail.mail']
        for lead in self:
            email_to = False
            company = lead.company_id

            for user in company.contact_user_ids:
                if user.partner_id.email:
                    if not email_to:
                        email_to = user.partner_id.name+' <'+user.partner_id.email+'>'
                    else:
                        email_to += ', '+user.partner_id.name+' <'+user.partner_id.email+'>'

            if not email_to:
                continue

            template = self.env.ref('odes_poc_website.mail_template_lead_contact_us', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(lead.id, force_send=True, email_values={'email_to': email_to})


class Company(models.Model):
    _inherit = "res.company"

    contact_user_ids = fields.Many2many('res.users', 'email_company_user_rel', 'company_id', 'user_id', string='Contact Us Users')
    email_alternative = fields.Char(string='Email Alternative')
    
