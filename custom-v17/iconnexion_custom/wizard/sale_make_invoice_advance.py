# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import html2plaintext


class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = "sale.advance.payment.inv"
	
	def _prepare_invoice_line_values_customize_bank_charge(self, order, name, amount, so_line):
		invoice_line_vals = 0, 0, {
				'name': html2plaintext(so_line.name) + ' Bank Charge ' + str(self.amount) + ' %',
				'price_unit': amount,
				'quantity': 1.0,
				'product_id': self.product_id.id,
				'product_uom_id': so_line.product_uom.id,
				'tax_ids': [(6, 0, so_line.tax_id.ids)],
				'sale_line_ids': [(6, 0, [so_line.id])],
				'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
				'analytic_account_id': order.analytic_account_id.id or False,
			},
		
		return invoice_line_vals


	def _create_invoice(self, order, so_line, amount):
		if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
			raise UserError(_('The value of the down payment amount must be positive.'))

		amount, name = self._get_advance_details(order)
		context = dict(self._context or {})
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
		
		
		is_iconnexion = False
		sale_order_id = False
		sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
		for sale in sale_orders:
			if sale.is_iconnexion:
				is_iconnexion = True
				sale_order_id = sale.id
				break
		if is_iconnexion and sale_order_id:
			context['sale_order_id'] = sale_order_id

		if order.fiscal_position_id:
			invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
		invoice = self.env['account.move'].sudo().with_context(context).create(invoice_vals).with_user(self.env.uid)
		invoice.message_post_with_view('mail.message_origin_link',
					values={'self': invoice, 'origin': order},
					subtype_id=self.env.ref('mail.mt_note').id)
		return invoice