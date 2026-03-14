# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class OdesSaleLinkPoToSupplier(models.TransientModel):
    _name = "odes.sale.link.po.to.supplier"
    _description = "Link PO to Supplier Wizard"

    order_line = fields.Char('Order Line')
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    line_ids = fields.One2many('odes.sale.link.po.to.supplier.line','wizard_id', string="Wizard")
    

    def action_confirm(self):
        count_checked = [x.id for x in self.line_ids if x.is_checked]
        if len(count_checked) != 1:
            raise UserError(_('Please select one Record'))
            
        for line in self.line_ids:
            if line.is_checked:
                if self.sale_order_line_id:
                    self.sale_order_line_id.write({'purchase_order_line_id':line.purchase_order_line_id.id})
                break


    def action_remove_link(self):
        if self.sale_order_line_id:
            self.sale_order_line_id.write({'purchase_order_line_id':False})
        return False

class OdesSaleLinkPoToSupplierLine(models.TransientModel):
    _name = "odes.sale.link.po.to.supplier.line"
    _description = "Link PO to Supplier Wizard Line"

    wizard_id = fields.Many2one('odes.sale.link.po.to.supplier', string="Wizard")
    purchase_number = fields.Char('PO No.')
    purchase_order_line_id = fields.Many2one('purchase.order.line', string="Product")
    purchase_currency_id = fields.Many2one('res.currency', string="Currency")
    purchase_qty = fields.Float('Qty')
    purchase_price_unit = fields.Float(string='Cost Price', digits='Product Price')
    is_checked = fields.Boolean("Is Checked?")
