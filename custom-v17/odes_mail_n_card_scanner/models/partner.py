# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import poplib
from ssl import SSLError
from socket import gaierror, timeout
from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'


    namecard_image = fields.Binary("Name Card",copy=False)


