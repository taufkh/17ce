# -*- coding: utf-8 -*- 
import time
import string
import urllib
import io
import tempfile
import csv
import xlrd
import re 

import werkzeug

import json
import logging
import base64
import datetime
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo import http 
from odoo.exceptions import AccessError, UserError
import ast
from odoo.tools import float_is_zero, ustr

from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response

import mimetypes
from odoo.tools.mimetypes import guess_mimetype
from dateutil.parser import parse
from operator import itemgetter

from odoo.addons.website.controllers.main import Website
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager 
from odoo.addons.documents.controllers.main import ShareRoute  # Import the class


logger = logging.getLogger(__name__)



class OdesDocumentShareRoute(ShareRoute):


    @http.route(['/document/share/<int:share_id>/<token>'], type='http', auth='public')
    def share_portal(self, share_id=None, token=None):
        try:
            share = http.request.env['documents.share'].sudo().browse(share_id)
            available_documents = share._get_documents_and_check_access(token, operation='read')
            if available_documents is False:
                if share._check_token(token):
                    options = {
                        'expiration_date': share.date_deadline,
                        'author': share.create_uid.name,

                    }
                    return request.render('documents.not_available', options)
                else:
                    return request.not_found()


            state_obj = http.request.env['res.country']
            states = state_obj.search([])  

            options = {
                'base_url': http.request.env["ir.config_parameter"].sudo().get_param("web.base.url"),
                'token': str(token),
                'upload': share.action == 'downloadupload',
                'share_id': str(share.id),
                'author': share.create_uid.name,
                'country_list': states
            }

            if share.type == 'ids' and len(available_documents) == 1:
                options.update(document=available_documents[0], request_upload=True)

                return request.render("odes_document.download_single_page", options)
            else:
                options.update(all_button='binary' in [document.type for document in available_documents],
                               document_ids=available_documents,
                               request_upload=share.action == 'downloadupload' or share.type == 'ids')
                return request.render("odes_document.download_multiple_page", options)
        except Exception:
            logger.exception("Failed to generate the multi file share portal")
        return request.not_found()



    @http.route(["/document/download/<int:share_id>/<access_token>/<int:id>"],
                type='http', auth='public', methods=['GET'], website=True, csrf=False)
    def download_one(self, id=None, access_token=None, share_id=None, **kwargs):
        """
        used to download a single file from the portal multi-file page.

        :param id: id of the file
        :param access_token:  token of the share link
        :param share_id: id of the share link
        :return: a portal page to preview and download a single file.
        """
        try:
            document = self._get_file_response(id, share_id=share_id, share_token=access_token, field='datas')

            return document or request.not_found()

        except Exception:
            logger.exception("Failed to download document %s" % id)

        return request.not_found() 


    @http.route(["/document/download/all/<int:share_id>/<access_token>"], type='http', auth='public')
    def share_download_all(self, access_token=None, share_id=None):
        """
        :param share_id: id of the share, the name of the share will be the name of the zip file share.
        :param access_token: share access token
        :returns the http response for a zip file if the token and the ID are valid.
        """
        env = request.env
        try:
            share = env['documents.share'].sudo().browse(share_id)
            
            documents = share._get_documents_and_check_access(access_token, operation='read')
            if documents:
                return self._make_zip((share.name or 'unnamed-link') + '.zip', documents)
            else:
                return request.not_found()
        except Exception:
            logger.exception("Failed to zip share link id: %s" % share_id)
        return request.not_found()    


    
    @http.route(["/document/form/save"], type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def document_form_save(self, **post):
        response  = { 'success':False}
        env = request.env
        share_id = int(post.get('res_id'))
        doc_id = post.get('doc_id','False')
        token = post.get('token','None')
        download_type = post.get('download_type',False)
        share = env['documents.share'].sudo().browse(share_id)

        values = {}
        save_fields = ['first_name','last_name','email','phone','company']
        for field in save_fields:
            values[field] = post.get(field,'').strip()


        first_name = post.get('first_name')
        last_name = post.get('last_name')
        full_name = first_name + ' ' + last_name

        contact_values = {
            'name': full_name,
            'company_name': post.get('company'),
            'email': post.get('email'),
            'phone': post.get('phone'),
        }

        for doc in share.document_ids:
            mailing = env['mailing.contact'].sudo().create(contact_values)
            contact_id = mailing.id

            values['document_id'] = doc.id
            values['mailing_list'] = contact_id
            env['odes.document.guest'].sudo().create(values)    


            default_document_setting_id = env.user.company_id.document_mailing_list_id.id

            if default_document_setting_id:
                contact_list_values = {
                    'list_id': default_document_setting_id,
                    'contact_id': contact_id,
                }
                env['mailing.contact.subscription'].sudo().create(contact_list_values)

            response['success'] = True

        if response['success']:
            url = '#'
            if download_type == 'single':
                url = '/document/download/%s/%s/%s' % (str(share_id), str(token), str(doc_id))
            if download_type == 'multiple':
                url = '/document/download/all/%s/%s' % (str(share_id), str(token))

            response['url'] = url
                
        return json.dumps(response)




