# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import binascii
import contextlib
import datetime
import hmac
import ipaddress
import itertools
import json
import logging
import os
import time
from collections import defaultdict
from hashlib import sha256
from itertools import chain, repeat

import decorator
import passlib.context
import pytz
from lxml import etree
from lxml.builder import E

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from odoo.modules.module import get_module_resource
from odoo.osv import expression
from odoo.service.db import check_super
from odoo.tools import partition, collections, frozendict, lazy_property, image_process




class Users(models.Model):
    """ User class. A res.users record models an OpenERP user and is different
        from an employee.

        res.users class now inherits from res.partner. The partner model is
        used to store the data related to the partner: lang, name, address,
        avatar, ... The user model is now dedicated to technical data.
    """
    _inherit = "res.users"


    registration_id = fields.Char("Registration ID")

