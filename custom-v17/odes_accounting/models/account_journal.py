# -*- coding: utf-8 -*- 
import re
import base64
import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools import partition, pycompat
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)



class Journal(models.Model):
    _inherit = 'account.journal'
    
    logo_journal = fields.Binary('Logo For Invoice Report')
    
