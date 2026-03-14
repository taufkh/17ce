# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    #adding manufacture_part_no field to the product template, fields 
    #and function are simillar to default_code field in product template
    # manufacture_part_no = fields.Char(
    #     'Manufacture Part No', compute='_compute_manufacte_part_no',
    #     inverse='_set_manufacture_part_no', store=True)
    
    
    @api.depends('product_variant_ids.purchase_order_line_ids', 'product_variant_ids.purchase_order_line_ids.order_id.state', 'is_updated_data')
    def _get_last_purchase(self):
        for template in self:
            
            
            purchase_history_ids = []
            if template.product_variant_ids.ids:
                self.env.cr.execute("""select po.partner_id from purchase_order_line pol inner join purchase_order po on pol.order_id = po.id where pol.product_id in  %s  group by po.partner_id;""",(tuple(template.product_variant_ids.ids),))
                result_partner = self.env.cr.fetchall()
                if result_partner: 

                    for res_part in result_partner:
                        self.env.cr.execute("""
                            select pol.price_unit,  po.date_order, po.currency_id, pol.product_id, po.partner_id from purchase_order_line pol \
                            inner join purchase_order po on pol.order_id = po.id where pol.product_id in %s and po.partner_id = %s  \
                            group by pol.price_unit,  pol.product_id, po.date_order, po.currency_id, po.partner_id  order by po.date_order desc limit 1;
                        """,(tuple(template.product_variant_ids.ids),res_part[0]))
                        result = self.env.cr.fetchall()
                        if result:
                            self.env['odes.product.purchase'].search([('product_tmpl_id', '=', template.id)]).unlink()
                            for res in result:
                                purchase_history_ids.append((0, 0, {'amount': float(res[0]),'currency_id': res[2], 'date': res[1], 'product_id': res[3],'partner_id': res[4]}))

            template.purchase_history_ids = purchase_history_ids
            
            
    @api.depends('product_variant_ids.sale_order_line_ids', 'product_variant_ids.sale_order_line_ids.order_id.state', 'is_updated_data')
    def _get_last_sale(self):
        for template in self:
            
            
            sale_history_ids = []
            if template.product_variant_ids.ids:
                self.env.cr.execute("""select so.partner_id from sale_order_line sol inner join sale_order so on sol.order_id = so.id where sol.product_id in  %s  group by so.partner_id;""",(tuple(template.product_variant_ids.ids),))
                result_partner = self.env.cr.fetchall()

                if result_partner: 

                    for res_part in result_partner:
                        self.env.cr.execute("""
                            select sol.price_unit,  so.date_order, so.currency_id, sol.product_id, so.partner_id from sale_order_line sol \
                            inner join sale_order so on sol.order_id = so.id where sol.product_id in %s and so.partner_id = %s  \
                            group by sol.price_unit,  sol.product_id, so.date_order, so.currency_id, so.partner_id  order by so.date_order desc limit 1;
                        """,(tuple(template.product_variant_ids.ids),res_part[0]))

    #                    c
                        result = self.env.cr.fetchall()

                        if result:
                            self.env['odes.product.sale'].search([('product_tmpl_id', '=', template.id)]).unlink()
                            for res in result:
                                sale_history_ids.append((0, 0, {'amount': float(res[0]),'currency_id': res[2], 'date': res[1], 'product_id': res[3],'partner_id': res[4]}))

            template.sale_history_ids = sale_history_ids
            
    purchase_history_ids = fields.One2many('odes.product.purchase', 'product_tmpl_id', string='Purchase History', compute='_get_last_purchase', store=True)
    sale_history_ids = fields.One2many('odes.product.sale', 'product_tmpl_id', string='Sale History', compute='_get_last_sale', store=True)
    manufacture_part_no = fields.Char('Manufacture Part No')
    is_updated_data = fields.Boolean('Updated Data')
    


class ProductProduct(models.Model):
    _inherit = "product.product"
    
    sale_order_line_ids = fields.One2many('sale.order.line', 'product_id', help='Technical: used to compute.')
    
    
 
class OdesProductPurchase(models.Model):
    _name = "odes.product.purchase"
    _description = "Odes Product Purchase Summary"
    
    def view_detail(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("odes_accounting.action_odes_purchase_order_line_tree")

        action['domain'] = [
            ('product_id.product_tmpl_id', 'in', self.product_tmpl_id.ids),
        ]
        return action

    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    product_id = fields.Many2one('product.product', 'Product')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    partner_id = fields.Many2one('res.partner', 'Supplier')
    date = fields.Datetime('Last Purchase')
    
    
    
class OdesProductSale(models.Model):
    _name = "odes.product.sale"
    _description = "Odes Product Sale Summary"
    
    def view_detail(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("odes_accounting.action_odes_sale_order_line_tree")

        action['domain'] = [
            ('product_id.product_tmpl_id', 'in', self.product_tmpl_id.ids)
        ]
        return action

    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    product_id = fields.Many2one('product.product', 'Product')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    partner_id = fields.Many2one('res.partner', 'Customer')
    date = fields.Datetime('Last Sales')
