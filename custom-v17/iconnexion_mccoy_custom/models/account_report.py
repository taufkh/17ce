# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
import copy
import json
import io
import logging
import lxml.html
import datetime
import ast
from collections import defaultdict
from math import copysign

from dateutil.relativedelta import relativedelta

from odoo.tools.misc import xlsxwriter
from odoo import models, fields, api, _
from odoo.tools import config, date_utils, get_lang
from odoo.osv import expression
from babel.dates import get_quarter_names
from odoo.tools.misc import formatLang, format_date
from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'
    _description = 'Account Report'
    

    # def account_open_action(self, options, domain):
    #     assert isinstance(domain, (list, tuple))
    #     domain += [('date', '>=', options.get('date').get('date_from')),
    #             ('date', '<=', options.get('date').get('date_to')),
    #             ('state', '=', 'posted')]
    #     ctx = self.env.context.copy()
    #     ctx.update({'search_default_account': 1, 'search_default_groupby_date': 1})
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Journal Entries for Tax Audit'),
    #         'res_model': 'account.move',
    #         'views': [[self.env.ref('iconnexion_mccoy_custom.view_invoice_tax_tree').id, 'list'], [False, 'form']],
    #         'domain': domain,
    #         'context': ctx,
    #     }

    # def account_open_tax(self, options, params=None):
    #     active_id = int(str(params.get('id')).split('_')[0])
    #     tax = self.env['account.tax'].browse(active_id)
    #     domain = ['|', ('invoice_line_ids.tax_ids', 'in', [active_id]),
    #                 ('invoice_line_ids.tax_line_id', 'in', [active_id])]
    #     if tax.tax_exigibility == 'on_payment':
    #         domain += [('tax_exigible', '=', True)]
    #     return self.account_open_action(options, domain)
    
    def account_open_action(self, options, domain):
        assert isinstance(domain, (list, tuple))
        domain += [('date', '>=', options.get('date').get('date_from')),
                   ('date', '<=', options.get('date').get('date_to'))]
        if not options.get('all_entries'):
            domain += [('move_id.state', '=', 'posted')]

        ctx = self.env.context.copy()
        ctx.update({'search_default_account': 1, 'search_default_groupby_date': 1})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Tax Report - Declaration'),
            'res_model': 'account.move.line',
            'views': [[self.env.ref('iconnexion_mccoy_custom.view_iconn_mccoy_tax_report_line_tree').id, 'list'], [False, 'form']],
            'domain': domain,
            'context': ctx,
        }
    
    def account_open_tax(self, options, params=None):
        active_id = int(str(params.get('id')).split('_')[0])
        tax = self.env['account.tax'].browse(active_id)
        domain = [('tax_line_id', 'in', [active_id])]
        if tax.tax_exigibility == 'on_payment':
            domain += [('tax_exigible', '=', True)]
        return self.account_open_action(options, domain)


    def open_action(self, options, domain):
        assert isinstance(domain, (list, tuple))
        domain += [('date', '>=', options.get('date').get('date_from')),
                   ('date', '<=', options.get('date').get('date_to'))]
        if not options.get('all_entries'):
            domain += [('move_id.state', '=', 'posted')]

        ctx = self.env.context.copy()
        ctx.update({'search_default_account': 1, 'search_default_groupby_date': 1})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Tax Report - Declaration'),
            'res_model': 'account.move.line',
            'views': [[self.env.ref('iconnexion_mccoy_custom.view_iconn_mccoy_tax_report_line_tree').id, 'list'], [False, 'form']],
            'domain': domain,
            'context': ctx,
        }
