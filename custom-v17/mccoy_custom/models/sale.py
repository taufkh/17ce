# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"


    freight_account_tmp = fields.Char("Freight Account")
    is_dont_freight_account = fields.Boolean("Dont Have Freight Account")
    # is_dont_multiple = fields.Boolean("Don't Multiple")


    @api.model_create_multi
    def create(self, vals_list):
        records = super(SaleOrder, self).create(vals_list)
        for vals, rec in zip(vals_list, records):
            name = vals.get("name")
            if name and name != "New":
                rec.write({'name': name})
        return records

    # def action_confirm(self):
    #     for order in self:
    #         if order.is_dont_multiple:
    #             return super(SaleOrder, order).with_context(use_default=True).action_confirm()
    #         else:
    #             return super(SaleOrder, order).action_confirm()


    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        line_obj = self.env['sale.order.line']
        result = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        try:
            add_qty = float(add_qty)
        except:
            add_qty = 0
        try:
            set_qty = float(set_qty)
        except:
            set_qty = 0

        if self.website_id.is_website_mccoy and result['line_id']:
            try:
                line = line_obj.sudo().browse(result['line_id'])
                if line.product_id and line:
                    price_unit = line.product_id.sudo().get_actual_price(self.website_id.currency_id,line.product_uom_qty)
                    line.write({'price_unit':price_unit})
            except:
                return result
        return result


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    @api.onchange('product_id')
    def _onchange_mccoy_product(self):
        curr = self.env.user.company_id.currency_id
        if self.order_id.currency_id:
            curr = self.order_id.currency_id
        if self.product_id and self._context.get('quantity'):
            product_uom_qty = 1
            if self.product_id.moq_ids:
                product_uom_qty = self.product_id.get_min_qty_product()
            self.product_uom_qty = product_uom_qty
            price_unit = self.product_id.get_actual_price(curr,product_uom_qty)
            self.price_unit = price_unit


    @api.onchange('product_uom_qty')
    def _onchange_mccoy_qty(self):
        curr = self.env.user.company_id.currency_id
        if self.product_id:
            if self.order_id.currency_id:
                curr = self.order_id.currency_id
            qty = self.product_uom_qty
            # min_qty = self.product_id.get_min_qty_product()
            # qty_multiply = self.product_id.qty_multiply or 1
            # if qty <= min_qty:
            #     qty = min_qty
            # else:
            #     qty -= 1
            #     check_qty = qty - min_qty
            #     residual = check_qty % qty_multiply
            #     qty=(check_qty+min_qty-residual)+qty_multiply

            # self.product_uom_qty = qty
            price_unit = self.product_id.get_actual_price(curr,qty)
            self.price_unit = price_unit
