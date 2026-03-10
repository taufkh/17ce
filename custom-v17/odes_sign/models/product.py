# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import html2plaintext
import math
from datetime import timedelta

class Product(models.Model):
    _inherit = "product.product"

    def _get_companies_from_config(self, config_key):
        companies = self.env['res.company']
        raw_refs = (self.env['ir.config_parameter'].sudo().get_param(config_key) or '').strip()
        if not raw_refs:
            return companies
        for token in [x.strip() for x in raw_refs.split(',') if x.strip()]:
            if token.isdigit():
                companies |= self.env['res.company'].browse(int(token))
            else:
                company = self.env.ref(token, raise_if_not_found=False)
                if company and company._name == 'res.company':
                    companies |= company
        return companies.exists()


    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        res = super(Product, self).name_get()
        context_data = self.env.context
        short_name_companies = self._get_companies_from_config('odes_sign.purchase_short_name_company_refs')
        should_use_short_name = self.env.company in short_name_companies if short_name_companies else False
        if should_use_short_name:
            if 'params' in context_data and 'model' in context_data['params'] and context_data['params']['model'] == 'purchase.order':
                return [(template.id, '%s' % (template.default_code or template.name))
                    for template in self]
            if 'quotation_only' in context_data and context_data['quotation_only']:
                return [(template.id, '%s' % (template.default_code or template.name))
                    for template in self]

        return res
