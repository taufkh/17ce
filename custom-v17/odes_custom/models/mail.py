# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import base64
import datetime
import logging
import psycopg2
import smtplib
import threading
import re

from collections import defaultdict

from odoo import _, api, fields, models
from odoo import tools
from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    ###NOT USED###
    # @api.model
    # def create(self, vals):
    #     context = dict(self._context or {})
    #     company = self.env.company

    #     email_cc = vals.get('email_cc') or ''
    #     if context.get('mail_post_autofollow') and company.email_cc:
    #         vals['email_cc'] = company.email_cc + ', ' + email_cc

    #     return super(MailMail, self).create(vals)
    ###NOT USED (END)###