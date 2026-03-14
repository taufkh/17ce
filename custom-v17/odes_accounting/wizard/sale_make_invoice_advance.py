# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import html2plaintext


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    is_split_by_line = fields.Boolean('Split By Line', default=False)
    
    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        company = order.company_id
        quotation_type = order.quotation_type
        if quotation_type == 'service' and company.service_journal_id:
            res['journal_id'] = company.service_journal_id.id
        elif quotation_type == 'item' and company.component_journal_id:
            res['journal_id'] = company.component_journal_id.id

        return res
    
    def _prepare_invoice_values_customize(self, order, name, amount, so_line):
        company = order.company_id
        quotation_type = order.quotation_type
        invoice_vals = {
            'ref': order.client_order_ref,
            'move_type': 'out_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(order.partner_id.id)).id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_reference': order.reference,
            'invoice_payment_term_id': order.payment_term_id.id,
            'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            
        }
        if quotation_type == 'service' and company.service_journal_id:
            invoice_vals['journal_id'] = company.service_journal_id.id
        elif quotation_type == 'item' and company.component_journal_id:
            invoice_vals['journal_id'] = company.component_journal_id.id

        return invoice_vals
    
    def _prepare_invoice_line_values_customize(self, order, name, amount, so_line):
        invoice_line_vals = 0, 0, {
                'name': html2plaintext(so_line.name) + ' Down Payment ' + str(self.amount) + ' %',
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
                'is_split_by_line_downpayment': True,
            },
        

        return invoice_line_vals
    
    
    def _create_invoice(self, order, so_line, amount):
        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('The value of the down payment amount must be positive.'))

        amount, name = self._get_advance_details(order)
        
        if self.is_split_by_line:
            invoice_vals = self._prepare_invoice_values_customize(order, name, amount, so_line)
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            for sale in sale_orders:
                list_line = []
                for line in order.order_line:
                    if line.product_uom_qty > 0:
                        amount_percentage = (line.product_uom_qty * line.price_unit) * self.amount / 100
                        invoice_line_vals = self._prepare_invoice_line_values_customize(order, name, amount_percentage, line)
                        list_line.append(invoice_line_vals)

                invoice_vals['invoice_line_ids'] = list_line
            
        else:
            invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)
        
        
        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        print (invoice_vals, 'invoice_vals')
        invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice
    
    
