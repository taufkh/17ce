# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def create_pricelist(self):
        pricelist_obj = self.env['product.pricelist']
        for currency in self:
            pricelist_exist = pricelist_obj.search([('currency_id', '=', currency.id)], limit=1)
            if not pricelist_exist:
                pricelist_obj.create({'name': 'Public Pricelist', 'currency_id': currency.id,})

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ResCurrency, self).create(vals_list)
        for vals, rec in zip(vals_list, records):
            if vals.get('active'):
                rec.create_pricelist()
        return records

    def write(self, vals):
        if vals.get('active'):
            self.create_pricelist()

        return super(ResCurrency, self).write(vals)
