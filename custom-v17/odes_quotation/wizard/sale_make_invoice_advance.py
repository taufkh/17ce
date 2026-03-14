# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import html2plaintext


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    def _prepare_invoice_line_values_customize(self, order, name, amount, so_line):
        invoice_line_vals = 0, 0, {
                'name': html2plaintext(so_line.name) + ' Down Payment ' + str(self.amount) + ' %',
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                # v16: analytic_tag_ids removed; use analytic_distribution
                'analytic_account_id': order.analytic_account_id.id or False,
            },
        
        return invoice_line_vals