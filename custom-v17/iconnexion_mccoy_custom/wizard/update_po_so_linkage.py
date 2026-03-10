# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_round
from odoo.exceptions import AccessError, UserError, ValidationError
import re


class UpdatePOSOLinkage(models.TransientModel):
    _name = 'update.po.so.linkage'
    _description = 'Update Purchase Sale Linkage'
    
    name = fields.Char('Name')
    line_ids = fields.One2many('update.po.so.linkage.line', 'linkage_id', string="Lines")
    picking_id = fields.Many2one("stock.picking", "Picking")
    picking_type = fields.Selection(
        selection=[
            ('incoming', 'Receipt'),
            ('outgoing', 'Delivery'),
            ('internal', 'Internal'),
        ],
        string='Picking Type',
    )

    @api.model
    def default_get(self, fields):
        res = super(UpdatePOSOLinkage, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            picking = self.env['stock.picking'].browse(active_id)
            res['picking_id'] = picking.id
            res['picking_type'] = picking.picking_type_id.code

            move_ids = picking.move_ids_without_package
            line_defaults = []
            for move in move_ids:
                line_defaults.append((0, 0, {
                    'product_id': move.product_id.id,
                    'name': move.name,
                    'product_uom_qty': move.product_uom_qty,
                    'quantity_done': move.quantity_done,
                    'product_uom': move.product_uom.id,
                    'stock_move_id': move.id,
                    'sale_line_id': move.sale_line_id.id,
                    'purchase_line_id': move.purchase_line_id.id,
                }))
            res['line_ids'] = line_defaults

        return res
    
    def update_po_so_linkage(self):
        for linkage in self:
            for line in linkage.line_ids:
                if line.stock_move_id:
                    if linkage.picking_type == 'incoming':
                        line.stock_move_id.purchase_line_id = line.purchase_line_id.id
                    elif linkage.picking_type == 'outgoing':
                        line.stock_move_id.sale_line_id = line.sale_line_id.id
                    else:
                        raise ValidationError("Invalid operation: Please provide a valid sale or purchase line.")
                    



class UpdatePOSOLinkageLine(models.TransientModel):
    _name = 'update.po.so.linkage.line'
    _description = 'Update Purchase Sale Linkage Line'
    
    linkage_id = fields.Many2one("update.po.so.linkage", "Linkage")
    product_id = fields.Many2one("product.product", "Product")
    name = fields.Char('Name')
    product_uom_qty = fields.Float('Demand')
    quantity_done = fields.Float('Done')
    product_uom = fields.Many2one("uom.uom","Unit of Measure")
    stock_move_id = fields.Many2one("stock.move","Stock Move")
    sale_line_id = fields.Many2one("sale.order.line","Sale Line")
    purchase_line_id = fields.Many2one("purchase.order.line","Purchase Line")
    

