# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression




class MCCOYSubscribe(models.Model):
    _name = "mccoy.subscribe"
    _description = "McCoy Subscriber"


    name = fields.Char("Email",required=True)
    active = fields.Boolean("Active",default=True)
