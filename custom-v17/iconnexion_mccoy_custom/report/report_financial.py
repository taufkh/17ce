# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date
from dateutil.relativedelta import relativedelta
from itertools import chain
import json
from odoo.tools.misc import formatLang, format_date
from odoo.tools import config, date_utils, get_lang
from datetime import datetime



class GenericTaxReport(models.AbstractModel):
    _inherit = 'account.generic.tax.report'


    def _get_total_line_eval_dict(self, period_balances_by_code, period_date_from, period_date_to, options):
        """ Overridden in order to add the net profit of the period to the variables
        available for the computation of total lines in GST Return F5 report.
        """
        eval_dict = super(GenericTaxReport, self)._get_total_line_eval_dict(period_balances_by_code, period_date_from, period_date_to, options)

        if self.env.company.country_id.code == 'SG':
            net_profit_query = """select coalesce(-sum(balance), 0)
                                  from account_move_line aml
                                  join account_account account
                                  on account.id = aml.account_id
                                  join account_move move
                                  on move.id = aml.move_id
                                  where
                                  account.user_type_id in %(account_types)s
                                  and (%(show_draft)s or move.state = 'posted')
                                  and aml.date <= %(date_to)s
                                  and aml.date >= %(date_from)s
                                  and move.company_id = %(company_id)s;"""

            account_types = tuple(self.env['ir.model.data'].xmlid_to_res_id(xmlid) for xmlid in ['account.data_account_type_revenue', 'account.data_account_type_expenses', 'account.data_account_type_depreciation'])
            params = {
                'account_types': account_types,
                'show_draft': options['all_entries'],
                'date_to': period_date_to,
                'date_from': period_date_from,
                'company_id': self.env.company.id,
            }
            self.env.cr.execute(net_profit_query, params)
            eval_dict['apollo_net_profit'] = self.env.cr.fetchall()[0][0]

        return eval_dict

    def _get_columns_name(self, options):
        columns_header = super(GenericTaxReport, self)._get_columns_name(options)
        tax_report = self.env['account.tax.report'].browse(options['tax_report'])
        if tax_report.country_id.code == 'SG':
            columns_header.append({'name': 'SGD', 'class': 'number', 'style': 'white-space: pre;'})
        return columns_header

    def _build_total_line(self, report_line, balances_by_code, formulas_dict, hierarchy_level, number_periods, options):
        result = super(GenericTaxReport, self)._build_total_line(report_line, balances_by_code, formulas_dict, hierarchy_level, number_periods, options)
        tax_report = self.env['account.tax.report'].browse(options['tax_report'])
        if tax_report.country_id.code == 'SG':
            currency_origin = self.env.company.currency_id
            currency = self.env['res.currency'].search([('name','=',"SGD")],limit=1)
            column = result['columns'][len(result['columns'])-1]
            period_total = column['balance']
            date_to = options['date']['date_to']
            period_total_sgd = currency_origin.with_context(date=date_to).compute(period_total, currency)
            result['columns'].append({'name': '' if period_total is None else self.format_value(amount=period_total_sgd,currency=currency), 'style': 'white-space:nowrap;', 'balance': period_total_sgd or 0.0})
        return result

    def _build_tax_grid_line(self, grid_data, hierarchy_level):
        result = super(GenericTaxReport, self)._build_tax_grid_line(grid_data, hierarchy_level)
        if grid_data.get('obj'):
            if grid_data['obj'].report_id.country_id.code == 'SG':
                currency_origin = self.env.company.currency_id
                currency = self.env['res.currency'].search([('name','=',"SGD")],limit=1)
                column = result['columns'][len(result['columns'])-1]
                balance = column['balance']
                date_to = self._context['date_to']
                balance_sgd = currency_origin.with_context(date=date_to).compute(balance, currency)
                result['columns'].append({'name': '' if balance is None else self.format_value(amount=balance_sgd,currency=currency), 'style': 'white-space:nowrap;', 'balance': balance_sgd or 0.0})
        return result

    def _get_lines_by_grid(self, options, line_id, grids):
        date_to = options['date']['date_to']
        self.with_context(date_to=date_to)
        result = super(GenericTaxReport, self)._get_lines_by_grid(options, line_id, grids)
        tax_report = self.env['account.tax.report'].browse(options['tax_report'])
        currency_origin = self.env.company.currency_id
        currency = self.env['res.currency'].search([('name','=',"SGD")],limit=1)
        if tax_report.country_id.code == 'SG':
            count = 0
            for data in result:
                if data.get('level') == 1:
                    if len(result[count]['columns']) == 2:
                        balance = result[count]['columns'][1]['balance']
                        result[count]['columns'][1]['name'] = self.format_value(amount=balance,currency=currency)
                    elif len(result[count]['columns']) == 1:
                        balance = result[count]['columns'][0]['balance']
                        balance_sgd = currency_origin.with_context(date=date_to).compute(balance, currency)
                        result[count]['columns'].append({'name': '' if balance is None else self.format_value(amount=balance_sgd,currency=currency), 'style': 'white-space:nowrap;', 'balance': balance_sgd or 0.0})
                        result[count]['columns'][1]['name'] = self.format_value(amount=balance_sgd,currency=currency)
                count+=1


        return result