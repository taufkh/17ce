from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from operator import itemgetter
from itertools import groupby

class AccountMove(models.Model):
	_inherit = 'account.move'


	currency_rate = fields.Float(string='Current Rate')
	is_proforma_invoice = fields.Boolean('Proforma Invoice', copy=False,default=False)
	amount_dep_paid = fields.Monetary(string='Dep Paid', store=True, readonly=True, compute='_compute_amount_balance_partial')
	amount_dep_paid_2nd = fields.Monetary(string='2nd Dep Paid', store=True, readonly=True, compute='_compute_amount_balance_partial')
	amount_balance = fields.Monetary(string='Balance', store=True, readonly=True, compute='_compute_amount_balance_partial')
	sale_order_id = fields.Many2one('sale.order', 'Source Sale Order')
	is_pi_clear = fields.Boolean(related="sale_order_id.is_pi_clear", string="PI Clear", store=True)
	is_generate_proforma = fields.Boolean(related="sale_order_id.is_generate_proforma", string="TT Payment Terms", store=True)
	is_generate_proforma_to_process = fields.Boolean(related="sale_order_id.is_generate_proforma_to_process", string="TT Payment Terms to Process", store=True)
	is_generate_proforma_partial_before_delivery = fields.Boolean(related="sale_order_id.is_generate_proforma_partial_before_delivery", string="TT Partial Before Delivery Payment Terms", store=True)
	is_generate_proforma_partial = fields.Boolean(related="sale_order_id.is_generate_proforma_partial", string="TT Partial Payment Terms", store=True)



	def taxes(self):
		datas = []
		dot = []
		for i in self.invoice_line_ids:
			datas.append({
				'tax': i.tax_ids.amount,
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

	@api.depends('invoice_line_ids.price_total', 'invoice_payment_term_id')
	def _compute_amount_balance_partial(self):
		for order in self:
			if order.is_proforma_invoice == True and order.invoice_payment_term_id.payment_term_type == 'partial_before_delivery_term' and order.invoice_payment_term_id.dep_paid_1st != 0 and order.invoice_payment_term_id.dep_paid_2nd != 0 and order.sale_order_id.state == 'draft':
				amount_dep_paid = amount_balance = 0.0
				amount_dep_paid = - order.amount_total * (order.invoice_payment_term_id.dep_paid_1st / 100)
				amount_balance = order.amount_total + amount_dep_paid
				order.update({
					'amount_dep_paid': amount_dep_paid,
					'amount_balance': amount_balance,
				})
			if order.is_proforma_invoice == True and order.invoice_payment_term_id.payment_term_type == 'partial_before_delivery_term' and order.invoice_payment_term_id.dep_paid_1st != 0 and order.invoice_payment_term_id.dep_paid_2nd != 0 and order.sale_order_id.state == 'sale':
				amount_dep_paid_2nd = amount_balance = 0.0
				amount_dep_paid_2nd = - order.amount_total * (order.invoice_payment_term_id.dep_paid_2nd / 100)
				order.update({
					'amount_dep_paid_2nd': amount_dep_paid_2nd,
					'amount_balance': amount_balance,
				})

			if order.is_proforma_invoice == True and order.invoice_payment_term_id.payment_term_type == 'partial_cod_term' and order.sale_order_id.state == 'draft':
				amount_dep_paid = amount_balance = 0.0
				if order.invoice_payment_term_id.dep_paid_1st != 0: 
					amount_dep_paid = - order.amount_total * (order.invoice_payment_term_id.dep_paid_1st / 100)
					amount_balance = order.amount_total + amount_dep_paid
				else:
					raise ValidationError(
							_("Please set the first deposit percentage in %s!") % (order.invoice_payment_term_id.name))
				order.update({
					'amount_dep_paid': amount_dep_paid,
					'amount_balance': amount_balance,
				})

	def action_register_payment_proforma(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'PI Payment',
			'view_mode': 'tree,form',
			'res_model': 'account.payment',
			'domain': [('sale_id', '=', self.sale_order_id.id)],
			'context': {'default_sale_id':self.sale_order_id.id,
						'default_payment_type': 'inbound',
						'default_partner_type': 'customer',
						'default_partner_id': self.partner_id.id,
						'default_amount': - self.amount_dep_paid,						
						'default_company_id': self.company_id.id or self.env.company.id,
						}
			}
	
	def action_register_payment_proforma_so(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'PI Payment',
			'view_mode': 'tree,form',
			'res_model': 'account.payment',
			'domain': [('sale_id', '=', self.sale_order_id.id)],
			'context': {'default_sale_id':self.sale_order_id.id,
						'default_payment_type': 'inbound',
						'default_partner_type': 'customer',
						'default_partner_id': self.partner_id.id,
						'default_amount': - self.amount_dep_paid_2nd,						
						'default_company_id': self.company_id.id or self.env.company.id,
						}
			}
	
	def action_register_payment_proforma_quo(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'PI Payment',
			'view_mode': 'tree,form',
			'res_model': 'account.payment',
			'domain': [('sale_id', '=', self.sale_order_id.id)],
			'context': {'default_sale_id':self.sale_order_id.id,
						'default_payment_type': 'inbound',
						'default_partner_type': 'customer',
						'default_partner_id': self.partner_id.id,
						'default_amount': self.amount_total,						
						'default_company_id': self.company_id.id or self.env.company.id,
						}
			}


	@api.model
	def default_get(self, fields):
		result = super(AccountMove, self).default_get(fields)
		# currency_id = result.get('currency_id')
		res_currency = self.env['res.currency'].search([('name', '=', 'SGD')], limit=1, order='id DESC')
		# currency = self.env['res.currency'].browse(currency_id)
		if res_currency:
			result['currency_rate'] = res_currency.rate
		return result


	def auto_check_currency_rate(self):
		today = datetime.date.today()
		# res_currency_rate = self.env['res.currency.rate'].search([],limit=1,order='id DESC')
		res_currency = self.env['res.currency'].search([('name', '=', 'SGD')], order='id DESC')
		notifications = []
		for currency in res_currency:
			if currency.name == 'SGD':
				# sumDate = today - currency.name
				# countInt = int(sumDate.days)
				# if countInt > 30:
				# print(res_currency)
				message = _('Exchange Rate Must be Updated Every 1st Day of the Month \n (%s) ') % (currency.name)
				notifications.append([                
				(self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
				{'type': 'simple_notification', 'title': _('Warning Message'), 'message': message, 'sticky': True, 'warning': True}])
		self.env['bus.bus'].sendmany(notifications)


	def action_internal_proforma_invoice(self):
		action = self.env.ref('iconnexion_custom.proforma_invoice_view_action').read()[0]
		internal_is_proforma = self.env['account.move'].search([('is_proforma_invoice','=', True)])
		context = {
			'is_proforma_invoice' : True,
			'move_type' : 'out_invoice',
		}
		action['context'] = context
		return action


	

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	serial_numbers = fields.Integer(string='No.', compute='_compute_serial_number')


	@api.depends('sequence', 'move_id')
	def _compute_serial_number(self):
		for rec in self:
			rec.serial_numbers = 0
			if len(rec.sale_line_ids) >= 1 :
				for record in rec.sale_line_ids:
					rec.serial_numbers = record.serial_numbers
			#else:
			#	if rec.serial_numbers == 0:
			#		serial_no = 1
			#		for line in rec.mapped('move_id').invoice_line_ids:
			#			line.serial_numbers = serial_no
			#			serial_no += 1
		# for rec in self:
		# 	if rec.move_id:
		# 		if rec.move_id.invoice_origin:
		# 			print(rec.move_id.invoice_origin)
		# # else if :


