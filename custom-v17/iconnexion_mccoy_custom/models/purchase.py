# -*- coding: utf-8 -*-

import itertools
import logging

from datetime import date, datetime, timedelta
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression
from operator import itemgetter
from itertools import groupby


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    purchase_delivery_method_id = fields.Many2one('delivery.carrier', string='Delivery Method')
    purchase_freight_terms_id = fields.Many2one('delivery.carrier', string='Freight Terms Method')
    is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)
    is_mccoy = fields.Boolean(string="McCoy Company", compute='compute_is_mccoy', store=True)
    is_odes = fields.Boolean(string="Odes Company", compute='compute_is_odes', store=True)
    cpn = fields.Char(string='CPN', compute='_compute_cpn', store=True, readonly=True)

    def taxes(self):
        datas = []
        dot = []
        for i in self.order_line:
            datas.append({
                'tax':i.taxes_id.amount,
                'amount': i.price_subtotal,
                'dump': 'dump',
            })
        grouper = itemgetter("tax", "dump")
        for key, grp in groupby(sorted(datas, key = grouper), grouper):
            temp_dict = dict(zip(["tax","dump"], key))
            amount = 0
            for item in grp:
                amount += item["amount"]
            temp_dict["amount"] = amount
            dot.append(temp_dict)

        return dot

    @api.depends('order_line.name')
    def _compute_cpn(self):
        for record in self:
            record.cpn = ', '.join(order_line.name for order_line in record.order_line)

    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'carrier_id': self.purchase_delivery_method_id.id if self.is_mccoy or self.is_iconnexion else False,
            'freight_terms_id': self.purchase_freight_terms_id.id if self.is_mccoy or self.is_iconnexion else False,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }

    @api.depends('company_id')
    def compute_is_iconnexion(self):
        for picking in self:
            company_name = picking.company_id.name
            if company_name and 'iconnexion' in company_name.lower():
                picking.is_iconnexion = True
            else:
                picking.is_iconnexion = False


    @api.depends('company_id')
    def compute_is_mccoy(self):
        for picking in self:
            company_name = picking.company_id.name
            if company_name and 'mccoy' in company_name.lower():
                picking.is_mccoy = True
            else:
                picking.is_mccoy = False


    @api.depends('company_id')
    def compute_is_odes(self):
        for picking in self:
            company_name = picking.company_id.name
            if company_name and 'odes' in company_name.lower():
                picking.is_odes = True
            else:
                picking.is_odes = False

    @api.onchange('partner_id', 'company_id')
    def onchange_icon_partner_id(self):
        # Ensures all properties and fiscal positions
        # are taken with the company of the order
        # if not defined, with_company doesn't change anything.
        self = self.with_company(self.company_id)
        if not self.partner_id:
            self.fiscal_position_id = False
            if self.is_mccoy or self.is_iconnexion:
                self.purchase_delivery_method_id = False
                self.purchase_freight_terms_id = False
            if self.is_odes:
                self.freight_terms = False
        else:
            self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
            if self.is_mccoy or self.is_iconnexion:
                self.purchase_delivery_method_id = self.partner_id.purchase_delivery_method_id
                self.purchase_freight_terms_id = self.partner_id.purchase_freight_terms_id
            if self.is_odes:
                self.freight_terms = self.partner_id.freight_terms
        return {}

    @api.model
    def auto_confirm_purchase_orders(self):
        today = fields.Date.today()
        confirmation_date = today - timedelta(days=21)
        target_date = datetime(2023, 1, 1)
        orders_to_confirm = self.search([
            ('state', '=', 'draft'),
            ('date_order', '<=', confirmation_date),('create_date', '>=', target_date), ('amount_total', '!=', 0)
        ])
        if orders_to_confirm:
            orders_to_confirm.button_confirm()
    

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"


    buffer_stock_product = fields.Float('Buffer Stock Product', readonly=True, compute='_compute_buffer_stock_product')
    buffer_stock_ids = fields.Many2many(
        'buffer.stock.line', 
        string='Buffer Link', 
        compute='_compute_buffer_stock_ids',
    )
    buffer_stock_so_qty = fields.Float(compute='_compute_buffer_stock_so_qty', string='SO Quantity (Buffer)', digits='Product Unit of Measure')
    is_group_iconnexion_edit_purchase_delivery_date = fields.Boolean(string='Purchase Line Delivery Date Manager', compute='_compute_is_in_group')

    @api.constrains('state')
    def _unlink_purchase_order_line_linkage(self):
        for line in self:
            if line.state == 'cancel':
                buffer_stock_line = self.env['buffer.stock.line'].search([
                    ('purchase_order_line_id', '=', line.id)
                ])
                for buffer_line in buffer_stock_line:
                    unlink_operations_po = [(3, record.id) for record in line.icon_sale_ids]
                    unlink_operations_so = [(3, record.id) for record in buffer_line.sale_order_line_id.icon_purchase_ids]
                    buffer_line.sale_order_line_id.write({'icon_purchase_ids': unlink_operations_so})
                    buffer_line.sale_order_line_id.write({'icon_purchase_id': None})
                    line.write({'icon_sale_ids': unlink_operations_po})
                    buffer_line.unlink()

    #group function
    def _compute_is_in_group(self):
        for leads in self:
            if self.user_has_groups('iconnexion_mccoy_custom.group_iconnexion_edit_purchase_delivery_date'):
                leads.is_group_iconnexion_edit_purchase_delivery_date = True
            else:
                leads.is_group_iconnexion_edit_purchase_delivery_date = False


    def name_get(self):
        res = []
        for record in self:
            name = '%s - %s) %s' % (record.order_id.name ,record.serial_numbers, record.product_id.name)
            res.append((record.id, name))
        return res


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('order_id.name', operator, name), ('product_id.name', operator, name)]
        po_lines = self.search(domain + args, limit=limit)
        return po_lines.name_get()

    def _compute_buffer_stock_so_qty(self):
        for i in self:
            stock_used = sum(i.buffer_stock_ids.mapped('stock_used'))
            i.buffer_stock_so_qty = stock_used
        

    def _compute_buffer_stock_ids(self):
        for line in self:
            line.buffer_stock_ids = self.env['buffer.stock.line'].search([
                ('purchase_order_line_id', '=', line.id)
            ])

    def _compute_buffer_stock_product(self):
        for i in self:
            i.buffer_stock_product = i.product_qty - i.icon_so_line_qty
            if i.buffer_stock_product < 0:
                i.buffer_stock_product = 0
