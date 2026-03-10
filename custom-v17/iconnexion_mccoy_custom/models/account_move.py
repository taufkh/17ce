from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
from collections import defaultdict
from operator import itemgetter
from itertools import groupby
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'


	currency_sgd_id = fields.Many2one('res.currency', string='Currency (SGD)', default=lambda self: self.env.ref('base.SGD').id)
	amount_total_signed_sgd = fields.Monetary(string='Total (SGD)', compute='_compute_tax_amount_tax_report', currency_field='currency_sgd_id')
	amount_untaxed_signed_sgd = fields.Monetary(string='Tax Excluded (SGD)', compute='_compute_tax_amount_tax_report', currency_field='currency_sgd_id')
	tax_amount = fields.Monetary(string='Tax Amount', compute='_compute_tax_amount_tax_report', currency_field='currency_id')
	tax_amount_sgd = fields.Monetary(string='Tax Amount (SGD)', compute='_compute_tax_amount_tax_report', currency_field='currency_sgd_id')
	paid_amount = fields.Monetary(string='Paid Amount', compute='_compute_tax_amount_tax_report', currency_field='currency_id')
	paid_amount_sgd = fields.Monetary(string='Paid Amount (SGD)', compute='_compute_tax_amount_tax_report', currency_field='currency_sgd_id')
	tax_rate = fields.Char(string='Tax Rate', compute='_compute_tax_rate')
	delivery_method_id = fields.Many2one('delivery.carrier', string='Delivery Method')
	freight_terms_id = fields.Many2one('delivery.carrier', string='Freight Terms Method')
	is_mccoy = fields.Boolean(string="McCoy Company", compute='compute_is_mccoy', store=True)
	is_odes = fields.Boolean(string="Odes Company", compute='compute_is_odes', store=True)
	pi_payment_state = fields.Selection(related='sale_order_id.pi_payment_state', string='PI Payment Status')
	is_income = fields.Boolean("Is Income ?")
	delivery_order_id = fields.Many2one('stock.picking', string='Delivery Order No.')
	receipt_id = fields.Many2one('stock.picking', string='Receipt No.')
	account_balance_id = fields.Many2one('account.account', help="Account Used to counter balance journals")
	pay_to = fields.Char(string="Pay To")
	remarks = fields.Char(string="Remarks")
	journal_remarks = fields.Char(string="Journal Remarks")
	amount_text = fields.Text('Amount Text', compute="_compute_amount_text")

	@api.onchange('partner_id', 'pay_to')
	def onchange_partner_with_reference(self):
		for account in self:
			if account.move_type == 'in_receipt' and account.is_expense:
				existing_ref = account.ref or ''
				if '-' in existing_ref:
					existing_ref_before_dash = existing_ref.split('-')[0]
				else:
					existing_ref_before_dash = existing_ref
				if account.partner_id and not account.pay_to:
					account.ref = existing_ref_before_dash + '-' + account.partner_id.name
				elif account.pay_to and not account.partner_id:
					account.ref = existing_ref_before_dash + '-' + account.pay_to
				else:
					account.ref = existing_ref_before_dash

	@api.depends('amount_total')
	def _compute_amount_text(self):
		self.amount_text = self.currency_id.amount_to_text(self.amount_total) if self.amount_total else ''

	def action_print_expense_report(self):
		return self.env.ref('iconnexion_mccoy_custom.action_report_expense_input').report_action(self)

	@api.model
	def format_voucher_no_expense(self, name):
		if name:
			if '-' in name:
				filtered_text = name.split('-')[0]
			else:
				filtered_text = name
			return f"{filtered_text}"
		else:
			return ""

	@api.model
	def format_account_balance(self, name):
		if name:
			filtered_text = ''.join(char for char in name if char.isalpha() or char.isspace())
			return f"{filtered_text} Payment Voucher"
		else:
			return ""

	def copy(self, default=None):
		if default is None:
			default = {}
		if not isinstance(default, dict):
			default = dict(default)
		res = super(AccountMove, self).copy(default)
		res.message_post(body='This Entry was duplicated from %s' % (self.name))
		return res

	def action_view_proforma_invoice_payment(self):
		proforma_payments = self.env['account.payment'].search([('sale_id', '=', self.sale_order_id.id)], order='id DESC')

		action = self.env["ir.actions.actions"]._for_xml_id("iconnexion_custom.action_account_payments2")
		if len(proforma_payments) > 1:
			action['domain'] = [('id', 'in', proforma_payments.ids)]
		elif len(proforma_payments) == 1:
			form_view = [(self.env.ref('account.view_account_payment_form').id, 'form')]
			if 'views' in action:
				action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				action['views'] = form_view
			action['res_id'] = proforma_payments.id
		else:
			action = {'type': 'ir.actions.act_window_close'}  # NOTE: no-op close action; review if early return is better

		context = {
			'default_payment_type': 'inbound',
			'default_partner_type': 'customer',                
			'search_default_inbound_filter': 1,                
			'default_move_journal_types': ('bank', 'cash')
		}
		action['context'] = context
		return action

	@api.depends('posted_before', 'state', 'journal_id', 'date')
	def _compute_name(self):
		def journal_key(move):
			return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

		def date_key(move):
			return (move.date.year, move.date.month)

		grouped = defaultdict(  # key: journal_id, move_type
			lambda: defaultdict(  # key: first adjacent (date.year, date.month)
				lambda: {
					'records': self.env['account.move'],
					'format': False,
					'format_values': False,
					'reset': False
				}
			)
		)
		self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
		highest_name = self[0]._get_last_sequence() if self else False

		# Group the moves by journal and month
		for move in self:
			if not highest_name and move == self[0] and not move.posted_before:
				# In the form view, we need to compute a default sequence so that the user can edit
				# it. We only check the first move as an approximation (enough for new in form view)
				pass
			elif (move.name and move.name != '/') or move.state != 'posted':
				# Has already a name or is not posted, we don't add to a batch
				continue
			group = grouped[journal_key(move)][date_key(move)]
			if not group['records']:
				if not move.is_income:
					# Compute all the values needed to sequence this whole group
					move._set_next_sequence()
					group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
					group['reset'] = move._deduce_sequence_number_reset(move.name)
			group['records'] += move

		# Fusion the groups depending on the sequence reset and the format used because `seq` is
		# the same counter for multiple groups that might be spread in multiple months.
		final_batches = []
		for journal_group in grouped.values():
			for date_group in journal_group.values():
				if not final_batches or final_batches[-1]['format'] != date_group['format']:
					final_batches += [date_group]
				elif date_group['reset'] == 'never':
					final_batches[-1]['records'] += date_group['records']
				elif (
					date_group['reset'] == 'year'
					and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
				):
					final_batches[-1]['records'] += date_group['records']
				else:
					final_batches += [date_group]

		# Give the name based on previously computed values
		for batch in final_batches:
			if not move.is_income:
				for move in batch['records']:
					move.name = batch['format'].format(**batch['format_values'])
					batch['format_values']['seq'] += 1
				batch['records']._compute_split_sequence()

		self.filtered(lambda m: not m.name).name = '/'


	@api.onchange('invoice_line_ids', 'line_ids')
	def onchange_line_ids_income_expense(self):
		for move in self:
			if move.is_income and move.account_balance_id:
				raise UserError(_("Please remove the Account Balance before editing a line, and discard the changes."))
			if move.is_expense and move.account_balance_id:
				raise UserError(_("Please remove the Account Balance before editing a line, and discard the changes."))


	@api.onchange('account_balance_id')
	def onchange_line_ids(self):
		for move in self:
			journal = self.env['account.journal'].search([('default_account_id', '=', move.account_balance_id.id)], limit=1, order='id DESC')
			sales_journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1, order='id DESC')

			if not self.line_ids:
				return
			if move.is_income:
				if journal and move.account_balance_id:
					move.journal_id = journal
				if sales_journal and not move.account_balance_id:
					move.journal_id = sales_journal
				for line in self.line_ids:
					account_receivable = self.env['account.account'].search([('user_type_id', 'ilike', 'receivable'), ('company_id', '=', self.env.company.id)], limit=1)
					if line.account_id:
						receivable = line.account_id.user_type_id.type.lower() == 'receivable' or line.is_account_balance_line
						if receivable:
							if move.account_balance_id:
								line.account_id = move.account_balance_id.id
								line.is_account_balance_line = True
							if not move.account_balance_id:
								line.account_id = account_receivable.id
								line.is_account_balance_line = False
			if move.is_expense:
				for line in self.line_ids:
					account_payable = self.env['account.account'].search([('user_type_id', 'ilike', 'payable'), ('company_id', '=', self.env.company.id)], limit=1)
					if line.account_id:
						payable = line.account_id.user_type_id.type.lower() == 'payable' or line.is_account_balance_line
						if payable:
							if move.account_balance_id:
								line.account_id = move.account_balance_id.id
								line.is_account_balance_line = True
							if not move.account_balance_id:
								line.account_id = account_payable.id
								line.is_account_balance_line = False

	@api.model_create_multi
	def create(self, vals_list):
		for vals in vals_list:
			move_type = vals.get('move_type', self._context.get('default_move_type'))
			is_income = vals.get('is_income', self._context.get('default_is_income'))
			is_proforma_invoice = vals.get('is_proforma_invoice')

			if move_type == 'out_refund':
				sequence = self.env.company.company_sequence_customer_credit_note_id.code
				if sequence:
					name = self.env['ir.sequence'].next_by_code(sequence) or '/'
					vals['name'] = name
			if move_type == 'out_receipt' and is_income is True:
				sequence = self.env.company.company_sequence_income_input_id.code
				if sequence:
					name = self.env['ir.sequence'].next_by_code(sequence) or '/'
					vals['name'] = name
			if move_type == 'in_refund':
				sequence = self.env.company.vendor_credit_note_sequence_id.code
				if sequence:
					name = self.env['ir.sequence'].next_by_code(sequence) or '/'
					vals['name'] = name
			if move_type == 'out_invoice' and not is_proforma_invoice:
				standalone_sequence = self.env.company.delivery_order_invoice_sequence_id.code
				sequence_taiwan = self.env.company.delivery_order_invoice_taiwan_sequence_id.code
				sequence_india = self.env.company.delivery_order_invoice_india_sequence_id.code
				if standalone_sequence and not self.env.user.cs_invoice_sequence_type and not self._context.get('action_create_invoice_from_do'):
					name = self.env['ir.sequence'].next_by_code(standalone_sequence) or '/'
					if 'DO' in name:
						vals['name'] = name.replace('DO', 'INV')
				if sequence_taiwan and self.env.user.cs_invoice_sequence_type == 'invoice taiwan' and not self._context.get('action_create_invoice_from_do'):
					name = self.env['ir.sequence'].next_by_code(sequence_taiwan) or '/'
					vals['name'] = name
					if 'DOT' in name:
						vals['name'] = name.replace('DOT', 'INT')
				if sequence_india and self.env.user.cs_invoice_sequence_type == 'invoice india' and not self._context.get('action_create_invoice_from_do'):
					name = self.env['ir.sequence'].next_by_code(sequence_india) or '/'
					vals['name'] = name
					if 'DOI' in name:
						vals['name'] = name.replace('DOI', 'INI')
		return super(AccountMove, self).create(vals_list)
	
	@api.model
	def default_get(self, fields_list):
		defaults = super(AccountMove, self).default_get(fields_list)
		if self._context.get('default_move_type') == 'out_invoice':
			partner_id = self._context.get('default_partner_id')
			if partner_id:
				partner = self.env['res.partner'].browse(partner_id)
				defaults.update({
					'delivery_method_id': partner.property_delivery_carrier_id.id,
					'freight_terms_id': partner.freight_terms_id.id
				})
		return defaults

	@api.depends('company_id')
	def compute_is_mccoy(self):
		for account in self:
			company_name = account.company_id.name
			if company_name and 'mccoy' in company_name.lower():
				account.is_mccoy = True
			else:
				account.is_mccoy = False

	@api.depends('company_id')
	def compute_is_odes(self):
		for account in self:
			company_name = account.company_id.name
			if company_name and 'odes' in company_name.lower():
				account.is_odes = True
			else:
				account.is_odes = False


	def _compute_tax_rate(self):
		for move in self:
			tax_rates = set()
			for line in move.invoice_line_ids:
				for tax in line.tax_ids:
					tax_rates.add('{:.0%}'.format(tax.amount / 100))
			deduplicated_rates = sorted(set(tax_rates))
			move.tax_rate = ', '.join(deduplicated_rates)

	def _compute_tax_amount_tax_report(self):
		for move in self:
			move.amount_total_signed_sgd = move.amount_total_signed * move.currency_rate
			move.amount_untaxed_signed_sgd = move.amount_untaxed_signed * move.currency_rate
			move.tax_amount = move.amount_total_signed - move.amount_untaxed_signed
			move.tax_amount_sgd = move.amount_total_signed_sgd - move.amount_untaxed_signed_sgd
			move.paid_amount = move.amount_total - move.amount_residual
			move.paid_amount_sgd = move.paid_amount * move.currency_rate

	@api.onchange('invoice_date')
	def onchange_update_currency_rate(self):
		for account in self:
			res_currency = self.env['res.currency'].search([('name', '=', 'SGD')], limit=1, order='id DESC')
			if res_currency:
				month = fields.Date.from_string(account.invoice_date).strftime('%Y-%m')
				currency_rate = res_currency.rate_ids.filtered(lambda r: fields.Date.from_string(r.name).strftime('%Y-%m') == month)
				latest_currency_rate = sorted(currency_rate, key=lambda r: r.create_date, reverse=True)[:1]
				if currency_rate:
					account.currency_rate = latest_currency_rate[0].rate
				else:
					account.currency_rate = False

	def action_register_payment_proforma(self):
		self.ensure_one()
		total_amount = 0
		if self.sale_order_id:
			amount_ids = self.env['account.payment'].search([('sale_id','=',self.sale_order_id.id)])
			for amount in amount_ids:
				total_amount += amount.amount
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
						'default_amount': - self.amount_dep_paid - total_amount,                       
						'default_company_id': self.company_id.id or self.env.company.id,
						}
			}
	
	def action_register_payment_proforma_so(self):
		self.ensure_one()
		total_amount = 0
		if self.sale_order_id:
			amount_ids = self.env['account.payment'].search([('sale_id','=',self.sale_order_id.id)])
			for amount in amount_ids:
				total_amount += amount.amount
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
						'default_amount': - self.amount_dep_paid_2nd - total_amount,                       
						'default_company_id': self.company_id.id or self.env.company.id,
						}
			}

	def action_register_payment_proforma_quo(self):
		self.ensure_one()
		total_amount = 0
		if self.sale_order_id:
			amount_ids = self.env['account.payment'].search([('sale_id','=',self.sale_order_id.id)])
			for amount in amount_ids:
				total_amount += amount.amount
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
						'default_amount': self.amount_total - total_amount,                       
						'default_company_id': self.company_id.id or self.env.company.id,
						'default_ref': self.name,
						}
			}

	

	# def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
	# 	""" Compute the dynamic tax lines of the journal entry.

	# 	:param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
	# 	"""
	# 	self.ensure_one()
	# 	in_draft_mode = self != self._origin

	# 	def _serialize_tax_grouping_key(grouping_dict):
	# 		''' Serialize the dictionary values to be used in the taxes_map.
	# 		:param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
	# 		:return: A string representing the values.
	# 		'''
	# 		return '-'.join(str(v) for v in grouping_dict.values())

	# 	def _compute_base_line_taxes(base_line):
	# 		''' Compute taxes amounts both in company currency / foreign currency as the ratio between
	# 		amount_currency & balance could not be the same as the expected currency rate.
	# 		The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
	# 		:param base_line:   The account.move.line owning the taxes.
	# 		:return:            The result of the compute_all method.
	# 		'''
	# 		move = base_line.move_id

	# 		if move.is_invoice(include_receipts=True):
	# 			handle_price_include = True
	# 			sign = -1 if move.is_inbound() else 1
	# 			quantity = base_line.quantity
	# 			is_refund = move.move_type in ('out_refund', 'in_refund')
	# 			price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
	# 		else:
	# 			handle_price_include = False
	# 			quantity = 1.0
	# 			tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
	# 			is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
	# 			price_unit_wo_discount = base_line.amount_currency

	# 		balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
	# 			price_unit_wo_discount,
	# 			currency=base_line.currency_id,
	# 			quantity=quantity,
	# 			product=base_line.product_id,
	# 			partner=base_line.partner_id,
	# 			is_refund=is_refund,
	# 			handle_price_include=handle_price_include,
	# 		)

	# 		if move.move_type == 'entry':
	# 			repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
	# 			repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
	# 			tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
	# 			if tags_need_inversion:
	# 				balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
	# 				for tax_res in balance_taxes_res['taxes']:
	# 					tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

	# 		return balance_taxes_res

	# 	taxes_map = {}

	# 	# ==== Add tax lines ====
	# 	to_remove = self.env['account.move.line']
	# 	for line in self.line_ids.filtered('tax_repartition_line_id'):
	# 		grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
	# 		grouping_key = _serialize_tax_grouping_key(grouping_dict)
	# 		if grouping_key in taxes_map:
	# 			# A line with the same key does already exist, we only need one
	# 			# to modify it; we have to drop this one.
	# 			to_remove += line
	# 		else:
	# 			taxes_map[grouping_key] = {
	# 				'tax_line': line,
	# 				'amount': 0.0,
	# 				'tax_base_amount': 0.0,
	# 				'grouping_dict': False,
	# 			}
	# 	if not recompute_tax_base_amount:
	# 		self.line_ids -= to_remove

	# 	# ==== Mount base lines ====
	# 	for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
	# 		# Don't call compute_all if there is no tax.
	# 		if not line.tax_ids:
	# 			if not recompute_tax_base_amount:
	# 				line.tax_tag_ids = [(5, 0, 0)]
	# 			continue

	# 		compute_all_vals = _compute_base_line_taxes(line)

	# 		# Assign tags on base line
	# 		if not recompute_tax_base_amount:
	# 			line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

	# 		tax_exigible = True
	# 		for tax_vals in compute_all_vals['taxes']:
	# 			grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
	# 			grouping_key = _serialize_tax_grouping_key(grouping_dict)

	# 			tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
	# 			tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

	# 			if tax.tax_exigibility == 'on_payment':
	# 				tax_exigible = False

	# 			taxes_map_entry = taxes_map.setdefault(grouping_key, {
	# 				'tax_line': None,
	# 				'amount': 0.0,
	# 				'tax_base_amount': 0.0,
	# 				'grouping_dict': False,
	# 			})
	# 			taxes_map_entry['amount'] += tax_vals['amount']
	# 			taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
	# 			taxes_map_entry['grouping_dict'] = grouping_dict
	# 		if not recompute_tax_base_amount:
	# 			line.tax_exigible = tax_exigible

	# 	# ==== Pre-process taxes_map ====
	# 	taxes_map = self._preprocess_taxes_map(taxes_map)

	# 	# ==== Process taxes_map ====
	# 	for taxes_map_entry in taxes_map.values():
	# 		# The tax line is no longer used in any base lines, drop it.
	# 		if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
	# 			if not recompute_tax_base_amount:
	# 				self.line_ids -= taxes_map_entry['tax_line']
	# 			continue

	# 		currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

	# 		# Don't create tax lines with zero balance.
	# 		# if currency.is_zero(taxes_map_entry['amount']):
	# 		#     if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
	# 		#         self.line_ids -= taxes_map_entry['tax_line']
	# 		#     continue

	# 		# tax_base_amount field is expressed using the company currency.
	# 		tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

	# 		# Recompute only the tax_base_amount.
	# 		if recompute_tax_base_amount:
	# 			if taxes_map_entry['tax_line']:
	# 				taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
	# 			continue

	# 		balance = currency._convert(
	# 			taxes_map_entry['amount'],
	# 			self.company_currency_id,
	# 			self.company_id,
	# 			self.date or fields.Date.context_today(self),
	# 		)
	# 		to_write_on_line = {
	# 			'amount_currency': taxes_map_entry['amount'],
	# 			'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
	# 			'debit': balance > 0.0 and balance or 0.0,
	# 			'credit': balance < 0.0 and -balance or 0.0,
	# 			'tax_base_amount': tax_base_amount,
	# 		}

	# 		if taxes_map_entry['tax_line']:
	# 			# Update an existing tax line.
	# 			if tax_rep_lines_to_recompute and taxes_map_entry['tax_line'].tax_repartition_line_id not in tax_rep_lines_to_recompute:
	# 				continue

	# 			taxes_map_entry['tax_line'].update(to_write_on_line)
	# 		else:
	# 			# Create a new tax line.
	# 			create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
	# 			tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
	# 			tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)

	# 			if tax_rep_lines_to_recompute and tax_repartition_line not in tax_rep_lines_to_recompute:
	# 				continue

	# 			tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
	# 			taxes_map_entry['tax_line'] = create_method({
	# 				**to_write_on_line,
	# 				'name': tax.name,
	# 				'move_id': self.id,
	# 				'company_id': self.company_id.id,
	# 				'company_currency_id': self.company_currency_id.id,
	# 				'tax_base_amount': tax_base_amount,
	# 				'exclude_from_invoice_tab': True,
	# 				'tax_exigible': tax.tax_exigibility == 'on_invoice',
	# 				**taxes_map_entry['grouping_dict'],
	# 			})

	# 		if in_draft_mode:
	# 			taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


	def action_post(self):
		res = super(AccountMove, self).action_post()
		for invoice in self:
			if invoice:
				if invoice.move_type != 'entry':
					for line in invoice.invoice_line_ids:
						if len(line.tax_ids) == 0:
							if not line.display_type:
								raise UserError(_("User should choose zero rated tax instead."))
			if invoice.is_income:
				invoice.write({'payment_state' : 'paid'})
			if invoice.is_expense:
				invoice.write({'payment_state' : 'paid'})
		return res


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	

	currency_sgd_id = fields.Many2one('res.currency', string='Currency (SGD)', default=lambda self: self.env.ref('base.SGD').id)
	tax_amount = fields.Monetary(string='Tax Amount', compute='_compute_tax_amount_tax_report', currency_field='company_currency_id')
	currency_tax_base_amount = fields.Monetary(string="Currency Tax Base Amount", readonly=True, currency_field='currency_sgd_id', compute='_compute_tax_amount_tax_report')
	currency_tax_amount = fields.Monetary(string='Tax Amount (SGD Legacy)', compute='_compute_tax_amount_tax_report', currency_field='currency_sgd_id')
	exchange_rate = fields.Float("Exchange Rate",compute="_compute_str_exchange_rate", digits=(999,5))
	amount_real_tax = fields.Monetary("Amount Real Tax",compute="_compute_amount_real_tax", store=True, readonly=True, currency_field='company_currency_id')
	sgd_currency_id = fields.Many2one(
		comodel_name='res.currency',
		string="SGD Currency",
		compute="_compute_sgd_currency_id")
	amount_total_sgd = fields.Monetary(string="Amount (SGD)",compute="_compute_amount_total_sgd", store=True, readonly=True,
		currency_field='sgd_currency_id')
	amount_total_company_currency = fields.Monetary(string="Amount (USD)",compute="_compute_amount_total_company_currency", store=True, readonly=True,
		currency_field='company_currency_id')
	sgd_tax_amount = fields.Monetary(string="Tax Amount (SGD)",compute="_compute_usd_sgd_tax_amount", store=True, readonly=True,
		currency_field='sgd_currency_id')
	usd_tax_amount = fields.Monetary(string="Tax Amount (USD)",compute="_compute_usd_sgd_tax_amount", store=True, readonly=True,
		currency_field='company_currency_id')
	is_account_balance_line = fields.Boolean("Account Balance Line")
	

	@api.depends('tax_base_amount','balance','amount_currency','price_total','price_subtotal')
	def _compute_usd_sgd_tax_amount(self):
		for data in self:
			sgd_tax_amount = 0
			usd_tax_amount = 0
			if isinstance(data.name, str) and '100%' in data.name:
				if data.tax_base_amount:
					tax_base_amount = data.tax_base_amount
					sgd_tax_amount = data.company_currency_id._convert(tax_base_amount, data.sgd_currency_id, data.company_id,data.date)
					usd_tax_amount = data.company_currency_id._convert(tax_base_amount, data.company_currency_id, data.company_id,data.date)
				elif data.sgd_currency_id == data.currency_id:
					sgd_tax_amount = data.amount_currency
					usd_tax_amount = data.company_currency_id._convert(data.balance, data.company_currency_id, data.company_id,data.date)
				else:
					balance = data.balance
					sgd_tax_amount = data.company_currency_id._convert(balance, data.sgd_currency_id, data.company_id,data.date)
					usd_tax_amount = data.company_currency_id._convert(data.balance, data.company_currency_id, data.company_id,data.date)
				if sgd_tax_amount < 0:
					sgd_tax_amount = sgd_tax_amount * -1 
				data.sgd_tax_amount = sgd_tax_amount
				if usd_tax_amount < 0:
					usd_tax_amount = usd_tax_amount * -1 
				data.usd_tax_amount = usd_tax_amount
			else:
				if data.tax_base_amount:
					sgd_tax_amount = data.company_currency_id._convert(data.balance, data.sgd_currency_id, data.company_id,data.date)
					usd_tax_amount = data.balance
				else:
					price_subtotal = data.price_subtotal
					price_total = data.price_total
					if price_total== price_subtotal:
						sgd_tax_amount = 0
						usd_tax_amount = 0
					else:
						diff = price_total-price_subtotal
						sgd_tax_amount = data.currency_id._convert(diff, data.sgd_currency_id, data.company_id,data.date)
						usd_tax_amount = data.currency_id._convert(diff, data.company_currency_id, data.company_id,data.date)

				if sgd_tax_amount < 0:
					sgd_tax_amount = sgd_tax_amount * -1 
				if usd_tax_amount < 0:
					usd_tax_amount = usd_tax_amount * -1 


			data.sgd_tax_amount = sgd_tax_amount
			data.usd_tax_amount = usd_tax_amount

	@api.depends('tax_base_amount','balance','amount_currency')
	def _compute_amount_total_sgd(self):
		for data in self:
			record = data
			amount_total_sgd = 0
			if isinstance(data.name, str) and '100%' in data.name:
				amount_total_sgd = 0
			else:
				if data.tax_base_amount:
					tax_base_amount = data.tax_base_amount
					amount_total_sgd = data.company_currency_id._convert(tax_base_amount, data.sgd_currency_id, data.company_id,data.date)
				elif data.sgd_currency_id == data.currency_id:
					amount_total_sgd = data.amount_currency
				else:
					balance = data.balance
					amount_total_sgd = data.company_currency_id._convert(balance, data.sgd_currency_id, data.company_id,data.date)
				if amount_total_sgd < 0:
					amount_total_sgd = amount_total_sgd * -1 
			data.amount_total_sgd = amount_total_sgd

	@api.depends('tax_base_amount','balance','amount_currency')
	def _compute_amount_total_company_currency(self):
		for data in self:
			amount_total_company_currency = 0
			record = data
			if isinstance(data.name, str) and '100%' in data.name:
				amount_total_company_currency = 0
			else:
				if data.tax_base_amount:
					tax_base_amount = data.tax_base_amount
					amount_total_company_currency = data.company_currency_id._convert(tax_base_amount, data.company_currency_id, data.company_id,data.date)
				else:
					balance = data.balance
					amount_total_company_currency = data.company_currency_id._convert(balance, data.company_currency_id, data.company_id,data.date)
				if amount_total_company_currency < 0:
					amount_total_company_currency = amount_total_company_currency * -1 
			data.amount_total_company_currency = amount_total_company_currency

	@api.depends('tax_base_amount','balance')
	def _compute_amount_real_tax(self):
		for data in self:
			if data.tax_base_amount:
				amount_real_tax = data.tax_base_amount
			else:
				balance = data.balance
				if balance < 0:
					balance=-1*balance
				amount_real_tax = balance
			data.amount_real_tax = amount_real_tax


	def _compute_sgd_currency_id(self):
		for data in self:
			sgd_currency_id = self.env.ref('base.SGD').id
			data.sgd_currency_id = sgd_currency_id


	def _compute_str_exchange_rate(self):
		for data in self:
			exchange_rate = round((data.move_id.amount_total_signed)/data.move_id.amount_total,5)
			if exchange_rate < 0:
				exchange_rate= exchange_rate * -1
			data.exchange_rate = exchange_rate


	def _compute_tax_amount_tax_report(self):
		for line in self:
			if line.currency_sgd_id:
				month = fields.Date.from_string(line.date).strftime('%Y-%m')
				currency_rate = line.currency_sgd_id.rate_ids.filtered(lambda r: fields.Date.from_string(r.name).strftime('%Y-%m') == month)
				latest_currency_rate = sorted(currency_rate, key=lambda r: r.create_date, reverse=True)[:1]
				if currency_rate:
					rates = latest_currency_rate[0].rate
				else:
					rates = 0.0
			else:
				rates = 0.0

			if line.tax_line_id.amount_type == 'fixed':
				line.tax_amount = line.tax_base_amount * line.tax_line_id.amount
			elif line.tax_line_id.amount_type == 'percent':
				line.tax_amount = line.tax_base_amount * (line.tax_line_id.amount / 100.0)
			else:
				line.tax_amount = 0.0
			
			line.currency_tax_base_amount = rates * line.tax_base_amount

			if line.tax_line_id.amount_type == 'fixed':
				line.currency_tax_amount = line.currency_tax_base_amount * line.tax_line_id.amount
			elif line.tax_line_id.amount_type == 'percent':
				line.currency_tax_amount = line.currency_tax_base_amount * (line.tax_line_id.amount / 100.0)
			else:
				line.currency_tax_amount = 0.0


class AccountPayment(models.Model):
	_inherit = 'account.payment'

	def action_post(self):     
		res = super(AccountPayment, self).action_post()
		if self.sale_id:
			account_move = self.env['account.move'].search([('sale_order_id', '=', self.sale_id.id), ('is_proforma_invoice', '=', True)], limit=1, order='id DESC')
			total_payment_amount = sum(payment.amount for payment in self.env['account.payment'].search([('sale_id', '=', self.sale_id.id)]))
			pi_payment_state = 'not_paid'

			if account_move:
				if total_payment_amount != 0:
					if account_move.amount_dep_paid == 0 and account_move.amount_dep_paid_2nd == 0:
						if total_payment_amount == account_move.amount_total:
							pi_payment_state = 'paid'
							self.sale_id.write({'is_pi_clear': True})
						elif total_payment_amount < account_move.amount_total:
							pi_payment_state = 'partial'
							self.sale_id.write({'is_pi_clear': False})
					elif account_move.amount_dep_paid != 0 and account_move.amount_dep_paid_2nd == 0:
						if total_payment_amount == - account_move.amount_dep_paid:
							pi_payment_state = 'paid'
							self.sale_id.write({'is_pi_clear': True})
						elif total_payment_amount < - account_move.amount_dep_paid:
							pi_payment_state = 'partial'
							self.sale_id.write({'is_pi_clear': False})
					elif account_move.amount_dep_paid == 0 and account_move.amount_dep_paid_2nd != 0:
						if total_payment_amount == - account_move.amount_dep_paid_2nd:
							pi_payment_state = 'paid'
							self.sale_id.write({'is_pi_clear': True})
						elif total_payment_amount < - account_move.amount_dep_paid_2nd:
							pi_payment_state = 'partial'
							self.sale_id.write({'is_pi_clear': False})
				self.sale_id.write({'pi_payment_state': pi_payment_state})
			for account in self.sale_id:
				partner_ids = []
				for cs in self.company_id.icon_customer_service_ids:
					partner_ids.append(cs.id)
				for finance in self.company_id.icon_finance_ids:
					partner_ids.append(finance.id)
				if partner_ids:
					account_move.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
						'iconnexion_mccoy_custom.finance_cs_notif_paid_pi',
						values={'invoice': account_move,},
						subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
						partner_ids=partner_ids,notify = False,
						subject='PI has been paid '+ account.name,                            
					)
		
		return res


	def action_draft(self):     
		res = super(AccountPayment, self).action_draft()
		if self.sale_id:
			account_move = self.env['account.move'].search([('sale_order_id', '=', self.sale_id.id), ('is_proforma_invoice', '=', True)], limit=1, order='id DESC')
			total_payment_amount = sum(payment.amount for payment in self.env['account.payment'].search([('sale_id', '=', self.sale_id.id), ('state', '=', 'posted')]))
			pi_payment_state = 'not_paid'
			pi_clear = False
			if account_move:
				if total_payment_amount != 0:
					if account_move.amount_dep_paid == 0 and account_move.amount_dep_paid_2nd == 0:
						if total_payment_amount == account_move.amount_total:
							pi_payment_state = 'paid'
							pi_clear = True
							self.sale_id.write({'is_pi_clear': pi_clear})
						elif total_payment_amount < account_move.amount_total:
							pi_payment_state = 'partial'
							pi_clear = False
							self.sale_id.write({'is_pi_clear': pi_clear})
					elif account_move.amount_dep_paid != 0 and account_move.amount_dep_paid_2nd == 0:
						if total_payment_amount == - account_move.amount_dep_paid:
							pi_payment_state = 'paid'
							pi_clear = True
							self.sale_id.write({'is_pi_clear': pi_clear})
						elif total_payment_amount < - account_move.amount_dep_paid:
							pi_payment_state = 'partial'
							pi_clear = False
							self.sale_id.write({'is_pi_clear': pi_clear})
					elif account_move.amount_dep_paid == 0 and account_move.amount_dep_paid_2nd != 0:
						if total_payment_amount == - account_move.amount_dep_paid_2nd:
							pi_payment_state = 'paid'
							pi_clear = True
							self.sale_id.write({'is_pi_clear': pi_clear})
						elif total_payment_amount < - account_move.amount_dep_paid_2nd:
							pi_payment_state = 'partial'
							pi_clear = False
							self.sale_id.write({'is_pi_clear': pi_clear})
				self.sale_id.write({'is_pi_clear': pi_clear})
				self.sale_id.write({'pi_payment_state': pi_payment_state})
		return res
	
	def compute_amount_residual(self):
		for move_payment in self:
			amount_residual = move_payment.account_payable_or_receivable.amount_residual_currency
			move_payment.amount_residual = abs(amount_residual)
			if move_payment.sale_id and move_payment.state == 'posted':
				move_payment.amount_residual = 0
