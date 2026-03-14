
from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast
import requests
import json
import base64
from odoo.tools.mimetypes import guess_mimetype

class OdesCardScannerWizard(models.TransientModel):
    _name = "odes.card.scanner.wizard"
    _description = "ODES Card Scanner Wizard"

    name = fields.Char("Name")
    image = fields.Binary("Image")
    response = fields.Char("Response")



    def card_scanner(self):
        obj = self.env['odes.card.scanner.contact.wizard']
        url = "https://app.covve.com/api/businesscards/scan"
        Authorization = self.env['ir.config_parameter'].sudo().get_param('odes_mail_n_card_scanner.api_key_covve')
        headers = {
          'Authorization': Authorization
        }
        decoded_data = base64.b64decode(self.image)
        mimetype = guess_mimetype(decoded_data)
        if 'image/' not in mimetype:
            raise ValidationError("Only allowed upload image/photo.")
        binaryimage = self.image.decode().encode("ascii")
        binaryimage = base64.decodebytes(binaryimage)
        files=[
          ('image',(self.name,binaryimage,mimetype))
        ]
        response = requests.request("POST", url, headers=headers, data={}, files=files)
        try:
            response = response.json()
        except:
            raise UserError(_('An error occurred during the scanning, please check photo and try to scan again.'))
        # print(response,'responseresponse')
        dict_create = {}
        dict_create['company_id'] = self.env.company.id
        dict_create['name'] = response['firstName']
        dict_create['notes'] = response['notes']

        if response['middleName']:
            dict_create['name']+=' '+response['middleName']
        if response['lastName']:
            dict_create['name']+=' '+response['lastName']

   
        phone_array = []
        for a_p in response['phones']:
            if  a_p.get('number'):
                phone_array.append(a_p.get('number'))
        dict_create['phones'] = ', '.join(phone_array)


        email_array = []
        for a_p in response['emails']:
            if  a_p.get('address'):
                email_array.append(a_p.get('address'))
        dict_create['emails'] = ', '.join(email_array)
                

        if response.get('jobs'):
            if response['jobs'][0].get('title'):
                dict_create['title'] = response['jobs'][0].get('title')

        if response.get('jobs'):
            if response['jobs'][0].get('company'):
                dict_create['company'] = response['jobs'][0].get('company')


        company_array = []
        for a_p in response['websites']:
            if  a_p.get('url'):
                company_array.append(a_p.get('url'))
        dict_create['website_company'] = ', '.join(company_array)



        addresses_array = []
        for a_p in response['addresses']:
            if  a_p.get('fullAddress'):
                addresses_array.append(a_p.get('fullAddress'))
        dict_create['addresses'] = ', '.join(addresses_array)
        dict_create['namecard_image'] = self.image

        languange = response['language']
        languange = languange.replace('zh','zh-CN')
        if languange != 'en':
            url_translate = "https://translation.googleapis.com/language/translate/v2?key="
            url_translate+= self.env['ir.config_parameter'].sudo().get_param('odes_mail_n_card_scanner.api_key_translations')
            for loop in dict_create:
                if loop != 'company_id' and loop != 'namecard_image':
                    data = {
                              "q": dict_create[loop],
                              "source": languange,
                              "target": 'en',
                              "format": "text"
                            }
                    headers = {'Content-Type':'application/json'}
                    res = requests.post(url_translate, data=json.dumps(data),headers=headers)
                    try:
                        translate = res.json()
                        translate = translate['data']['translations'][0]['translatedText']
                    except:
                        break
                    dict_create[loop] = translate

        result = obj.create(dict_create)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Result Name Scanner',
            'res_model': 'odes.card.scanner.contact.wizard',
            'views': [[self.env.ref('odes_mail_n_card_scanner.odes_card_scanner_contact_wizard_form_view').id, 'form']],
            'target': 'new',
            'res_id':result.id

        }




class OdesCardScannerContactWizard(models.TransientModel):
    _name = "odes.card.scanner.contact.wizard"
    _description = "ODES Card Scanner Contact Wizard"

    name = fields.Char("Name")
    company = fields.Char("Company")
    website_company = fields.Char("Website Company")
    emails = fields.Char("Emails")
    phones = fields.Char("Phones")
    title = fields.Char("Title")
    notes = fields.Char("Notes")
    addresses = fields.Char("Address")
    company_id = fields.Many2one("res.company", "Internal Company")
    namecard_image = fields.Binary("Name Card")

    def scan_again(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Card Scanner',
            'res_model': 'odes.card.scanner.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context':{'form_view_ref':'odes_mail_n_card_scanner.odes_card_scanner_wizard_form_view'},
        }



    def create_contact(self):
        contact_obj = self.env['res.partner']
        t_obj = self.env['res.partner.title']
        parent_id = False
        if self.company:
            check_parent = contact_obj.sudo().search([('name','=',self.company),('company_id','=',self.company_id.id)],limit=1)
            if check_parent:
                parent_id = check_parent.id
            else:
                parent = contact_obj.create({'name':self.company,'is_company':True,'website':self.website_company,'company_id':self.company_id.id})
                parent_id = parent.id
        title = t_obj.sudo().search([('name','=',self.title)],limit=1)
        if not title:
            title = t_obj.create({'name':self.title})
        contact = contact_obj.create({
            'parent_id' :parent_id,
            'title':title.id,
            'name':self.name,
            'namecard_image':self.namecard_image,
            'email':self.emails,
            'phone':self.phones,
            'company_id':self.company_id.id,
            'comment':self.notes})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contact',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id':contact.id

        }
