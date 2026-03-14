# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from psycopg2 import Error, OperationalError

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_round



class StockQuant(models.Model):
    _inherit = 'stock.quant'


    product_brand_id = fields.Many2one("product.brand","Brand",related='product_id.product_brand_id',store=True)
    wh_id = fields.Many2one("stock.warehouse", "Report Warehouse", compute='_compute_warehouse_id', store=True)


    @api.depends('location_id')
    def _compute_warehouse_id(self):
        wh_obj = self.env['stock.warehouse']
        for data in self:
            warehouse_id = False
            warehouse = wh_obj.sudo().search([('company_id','=',data.company_id.id),('lot_stock_id','=',data.location_id.id)],limit=1)
            if warehouse:
                warehouse_id = warehouse.id
            data.wh_id = warehouse_id

