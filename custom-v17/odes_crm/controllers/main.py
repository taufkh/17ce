from odoo import http
from odoo.http import request
from odoo import api, fields, models, _
from datetime import date, timedelta, datetime


class landingPage(http.Controller):

    @http.route('/whitepaper-landing-page/',type='http', website=True, csrf=False, auth='public')
    def whitepaper_landing_page(self, **kwargs):
        current_url = request.httprequest.path
        return request.render('odes_crm.landing_page',{
            'url' : current_url,
        })

    @http.route('/campaign-landing-page/process', type='http', website=True, csrf=False, auth='public')
    def process(self, **kwargs):
        
        if kwargs:
            data = {}
            url = kwargs.get('url','')
            website_obj = request.env['website.page'].sudo().search([('url', '=', url[:-1])], limit=1)
            
            if website_obj:
                mailing_contact_obj = request.env['mailing.contact'].sudo()
                new_contact = mailing_contact_obj.create({
                    'name' : kwargs.get('name',''),
                    'email' : kwargs.get('email',''),
                    'phone' : kwargs.get('phone',''),
                    'company_name' : kwargs.get('company',''),
                    # 'position' : kwargs.get('position',''),
                    'list_ids' : website_obj.mailing_list_id if website_obj.mailing_list_id else False,
                })

                crm_obj = request.env['crm.lead'].sudo()
                new_lead = crm_obj.create({
                    'name' : website_obj.mailing_list_id.name + ' - ' + kwargs.get('name',''),
                    'contact_name' : kwargs.get('name',''),
                    'email_from' : kwargs.get('email',''),
                    'phone' : kwargs.get('phone',''),
                    'partner_name' : kwargs.get('company',''),
                    'function' : kwargs.get('position',''),
                    'user_id': website_obj.user_id.id if website_obj.user_id else False,
                    'team_id': website_obj.team_id.id if website_obj.team_id else False,
                })

                data = {
                    'name' : kwargs.get('name',''),
                    'email' : kwargs.get('email',''),
                    'phone' : kwargs.get('phone',''),
                    'company' : kwargs.get('company',''),
                    'position' : kwargs.get('position',''),
                    'contact_id' : new_contact.id,
                    'lead_id' : new_lead.id,
                }

            return request.render('odes_crm.process', data)
    
    @http.route('/campaign-landing-page/success', type='http', website=True, csrf=False, auth='public')
    def schedule_demo(self, **kwargs):

        if kwargs:
            date = kwargs.get('preferred_date','')
            date = date.split('-')
            new_date = datetime(int(date[0]), int(date[1]), int(date[2]), 0, 0, 0, 0)

            preferred_date = new_date.strftime('%Y-%m-%d')

            contact_obj = request.env['mailing.contact'].sudo().browse(kwargs.get('contact_id',''))
            if contact_obj:
                contact_obj.write({
                    'preferred_date_to_call' : preferred_date,
                    'preferred_time_to_call' : kwargs.get('preferred_time',''),
                })

            lead_obj = request.env['mailing.contact'].sudo().browse(kwargs.get('lead_id',''))
            # if lead_obj:
            #     lead_obj.write({
            #         'preferred_date_to_call' : preferred_date,
            #         'preferred_time_to_call' : kwargs.get('preferred_time',''),
            #     })

            data = {
                'name' : kwargs.get('name',''),
                'email' : kwargs.get('email',''),
                'phone' : kwargs.get('phone',''),
                'company' : kwargs.get('company',''),
                'position' : kwargs.get('position',''),
                'preferred_date' : kwargs.get('preferred_date',''),
                'preferred_time' : kwargs.get('preferred_time',''),
                'contact_id' : kwargs.get('contact_id',''),
                'lead_id' : kwargs.get('lead_id',''),
            }

            return request.render('odes_crm.schedule_demo',{})

