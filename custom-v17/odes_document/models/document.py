# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import image_process
from ast import literal_eval
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import re
from urllib.parse import urlparse



class DocumentsInherit(models.Model):
    _inherit = "documents.document"

    ondrive_share_url = fields.Char('OnDrive Share Url')
    

    def action_show_guest_view(self):
        action = self.env.ref('odes_document.odes_document_guest_action').sudo().read()[0]
        action['domain'] = [('document_id', '=', self.id)]
        return action  


    def create_onedrive_directdownload (self, onedrive_link):
        data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
        data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
        resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
        return resultUrl

    def create_sharepoint_directdownload (self, onedrive_link):
        sharepoint_share_url = self.ondrive_share_url
        # resultUrl = re.sub(r"?\S+", "", sharepoint_share_url)
        url = urlparse(sharepoint_share_url)
        resultUrl = url.scheme + "://" + url.netloc + url.path
        resultUrl = resultUrl + '?download=1'
        return resultUrl


    @api.onchange('ondrive_share_url')
    def _onchange_ondrive_share_url(self):
        ondrive_share_url = self.ondrive_share_url
        
        if ondrive_share_url:
            if 'sharepoint' in ondrive_share_url:
                self.ondrive_share_url = ondrive_share_url
                self.url = self.create_sharepoint_directdownload(ondrive_share_url)
            else:
                print("Generate OnDrive URL")
                ondrive_share_url = ondrive_share_url.strip()

                invalid_url = ['google','dropbox',]
                if any([x in ondrive_share_url for x in invalid_url]):
                    raise UserError(_('Invalid OnDrive Url'))

                must_contain = ['https://']
                if not any([x in ondrive_share_url for x in must_contain]):
                    raise UserError(_('Invalid OnDrive Url'))

                self.ondrive_share_url = ondrive_share_url
                self.url = self.create_onedrive_directdownload(ondrive_share_url)


class DocumentsUploadUrlWizardInherit(models.TransientModel):
    _inherit = "documents.upload.url.wizard"

    ondrive_share_url = fields.Char('OnDrive Share Url')

    def create_onedrive_directdownload(self, onedrive_link):
        data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
        data_bytes64_String = data_bytes64.decode('utf-8').replace('/', '_').replace('+', '-').rstrip("=")
        resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
        return resultUrl

    def create_sharepoint_directdownload(self, onedrive_link):
        url = urlparse(ondrive_link)
        resultUrl = url.scheme + "://" + url.netloc + url.path
        resultUrl = resultUrl + '?download=1'
        return resultUrl

    @api.onchange('ondrive_share_url')
    def _onchange_ondrive_share_url_wizard(self):
        ondrive_share_url = self.ondrive_share_url

        if ondrive_share_url:
            if 'sharepoint' in ondrive_share_url:
                self.ondrive_share_url = ondrive_share_url
                self.url = self.create_sharepoint_directdownload(ondrive_share_url)
            else:
                ondrive_share_url = ondrive_share_url.strip()
                invalid_url = ['google', 'dropbox']
                if any(x in ondrive_share_url for x in invalid_url):
                    raise UserError(_('Invalid OnDrive Url'))

                if 'https://' not in ondrive_share_url:
                    raise UserError(_('Invalid OnDrive Url'))

                self.ondrive_share_url = ondrive_share_url
                self.url = self.create_onedrive_directdownload(ondrive_share_url)

