# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import image_process
from ast import literal_eval
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import re


class OdesDocumentGuest(models.Model):

    _name = "odes.document.guest"
    _description = "Guest Table"
    
    _rec_name = 'first_name'

    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    email = fields.Char('Email Address')
    country_id = fields.Many2one('res.country', string='Country')
    company = fields.Char('Company Name')
    phone = fields.Char('Phone Number')
    # your_team = fields.Selection(selection=[('team_analytics','Analytics or Data'),('team_sales','Sales'),('team_marketing','Marketing'),('team_product','Product'),('team_executive','Executive'),('team_other','Other')], string='Team')
    # download_reason = fields.Selection(selection=[('reason_analytics_tools','I already use analytics and am considering changing tools'),('reason_analytics_practices','I already use analytics and want to learn best practices'),('reason_noanalytics_tools','I don’t use analytics yet but am considering tools to get started'),('reason_noanalytics_learn','I don’t use analytics yet but want to learn more')], string='Download Reason')
    # is_opt_in = fields.Boolean('Opt In?')
    document_id = fields.Char("Doc ID")
    mailing_list = fields.Many2one('mailing.contact', string='Mailing List')

