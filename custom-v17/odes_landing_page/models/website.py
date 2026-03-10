# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import inspect
import logging
import hashlib
import re


from werkzeug import urls
from werkzeug.datastructures import OrderedMultiDict
from werkzeug.exceptions import NotFound

from odoo import api, fields, models, tools
from odoo.addons.http_routing.models.ir_http import slugify, _guess_mimetype, url_for
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.portal.controllers.portal import pager
from odoo.http import request
from odoo.modules.module import get_resource_path
from odoo.osv.expression import FALSE_DOMAIN
from odoo.tools.translate import _



class Website(models.Model):

    _inherit = "website"
    
    campaign_intelligent_automation_id = fields.Many2one("utm.campaign","Campaign Intelligent Automation")

