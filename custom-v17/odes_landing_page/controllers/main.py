
from odoo.http import request
import json

from odoo import api, fields, models, _, http
from odoo.exceptions import UserError
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.website_sale.controllers.main import Website

class OdesLandingPageWebsite(Website):

    # @http.route(['/intelligent-automation'], type='http', auth='public', website=True)
    # def intelligent_automation(self, **post):
    #     values = {'website_id':request.website.id or ''}
    #     crm_obj = request.env['crm.lead']
    #     return request.render('odes_landing_page.odes_intelligent_automation_page', values)


    @http.route(['/intelligent-automation-temporary'], type='http', auth="public", methods=['POST'], website=True,csrf=False)
    def intelligent_automation_temporary(self, **post):
        crm_obj = request.env['crm.lead']
        

    @http.route('/intelligent-automation-post', type='json', auth='public')
    def intelligent_automation_post(self, contact_name, phone, email, companyname,website_id=False):
        crm_obj = request.env['crm.lead']
        website_obj = request.env['website']
        campaign_id = False
        company_id = False
        if website_id:
            website=website_obj.browse(int(website_id))
            campaign_id = website.campaign_intelligent_automation_id.id or False
            company_id = website.company_id.id
        partner_id = request.env.user.partner_id.id
        try:
            crm_obj.sudo().create({
                'partner_id':partner_id,
                'contact_name':contact_name,
                'phone':phone,
                'email_from':email,
                'partner_name':companyname,
                'campaign_id':campaign_id,
                'type':'lead',
                'company_id':company_id,
                'name':contact_name,

            })
            return True
        except:
            return False