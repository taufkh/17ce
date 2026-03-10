# -*- coding: utf-8 -*-
from operator import is_
from odoo import api, fields, models, _, tools, SUPERUSER_ID

from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.osv.expression import AND
from collections import defaultdict
# from datetime import datetime
from datetime import datetime, timedelta
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta,FR,WE
from odoo.tools.misc import formatLang, get_lang
from functools import partial
from itertools import groupby


class StockPicking(models.Model):
	_inherit = "stock.picking"

	date_cogs = fields.Datetime(
		string="COGS Date",
		required=False, readonly=False, copy=False,store=True,      
		compute='_compute_date_cogs',inverse='_set_cogs_date')
	date_cogs2 = fields.Datetime(
		string="COGS Date Inverse")
	transfer_date = fields.Datetime(string="Transfer Date")
	freight_terms_id = fields.Many2one('delivery.carrier', string='Freight Terms Method')
	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)
	is_mccoy = fields.Boolean(string="McCoy Company", compute='compute_is_mccoy', store=True)
	is_odes = fields.Boolean(string="Odes Company", compute='compute_is_odes', store=True)
	invoice_count = fields.Integer(string="Invoice Count", compute='compute_invoice_count')
	bill_count = fields.Integer(string="Bill Count", compute='compute_bill_count')
	vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill')

	def action_update_po_so_link(self):
		return {
			'name': 'Update Linkage',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'update.po.so.linkage',
			'target': 'new',
			'context': {'active_id': self.id},
		}

	def compute_bill_count(self):
		for picking in self:
			account_move_obj = self.env['account.move'].search_count([('receipt_id', '=', picking.id)])
			picking.bill_count = account_move_obj

	def action_view_bill(self):
		invoices = self.env['account.move'].search([('receipt_id', '=', self.id)])
		action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
		if len(invoices) > 1:
			action['domain'] = [('id', 'in', invoices.ids)]
		elif len(invoices) == 1:
			form_view = [(self.env.ref('account.view_move_form').id, 'form')]
			if 'views' in action:
				action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				action['views'] = form_view
			action['res_id'] = invoices.id
		else:
			action = {'type': 'ir.actions.act_window_close'}  # NOTE: no-op close action; review if early return is better

		context = {
			'default_move_type': 'in_invoice',
		}
		if len(self) == 1:
			context.update({
				'default_partner_id': self.purchase_id.partner_id.id,
				'default_invoice_payment_term_id': self.purchase_id.payment_term_id.id or self.purchase_id.partner_id.property_supplier_payment_term_id.id or self.purchase_id.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
				'default_invoice_origin': self.purchase_id.mapped('name'),
				'default_user_id': self.purchase_id.user_id.id,
			})
		action['context'] = context
		return action

	def compute_invoice_count(self):
		for picking in self:
			account_move_obj = self.env['account.move'].search_count([('delivery_order_id', '=', picking.id)])
			picking.invoice_count = account_move_obj

	def action_view_invoice(self):
		invoices = self.env['account.move'].search([('delivery_order_id', '=', self.id)])
		action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
		if len(invoices) > 1:
			action['domain'] = [('id', 'in', invoices.ids)]
		elif len(invoices) == 1:
			form_view = [(self.env.ref('account.view_move_form').id, 'form')]
			if 'views' in action:
				action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				action['views'] = form_view
			action['res_id'] = invoices.id
		else:
			action = {'type': 'ir.actions.act_window_close'}  # NOTE: no-op close action; review if early return is better

		context = {
			'default_move_type': 'out_invoice',
		}
		if len(self) == 1:
			context.update({
				'default_partner_id': self.sale_id.partner_id.id,
				'default_partner_shipping_id': self.sale_id.partner_shipping_id.id,
				'default_invoice_payment_term_id': self.sale_id.payment_term_id.id or self.sale_id.partner_id.property_payment_term_id.id or self.sale_id.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
				'default_invoice_origin': self.sale_id.mapped('name'),
				'default_user_id': self.sale_id.user_id.id,
			})
		action['context'] = context
		return action

	_sql_constraints = [
		('name_uniq', 'Check(1=1)', 'Reference must be unique per company!'),
	]


	@api.constrains('state')
	def onchange_running_number(self):
		for picking in self:
			if picking.state == 'done' and picking.name.lower() == 'draft' and (picking.is_iconnexion or picking.is_mccoy):
				sequence = self.env.company.delivery_order_invoice_sequence_id.code
				sequence_taiwan = self.env.company.delivery_order_invoice_taiwan_sequence_id.code
				sequence_india = self.env.company.delivery_order_invoice_india_sequence_id.code
				user = self.env.user
				if sequence and not user.cs_invoice_sequence_type:
					name = self.env['ir.sequence'].next_by_code(sequence) or '/'
					picking.name = name
				if sequence_taiwan and user.cs_invoice_sequence_type == 'invoice taiwan':
					name = self.env['ir.sequence'].next_by_code(sequence_taiwan) or '/'
					picking.name = name
				if sequence_india and user.cs_invoice_sequence_type == 'invoice india':
					name = self.env['ir.sequence'].next_by_code(sequence_india) or '/'
					picking.name = name

	@api.model_create_multi
	def create(self, vals_list):
		context = dict(self._context or {})
		for vals in vals_list:
			picking_type_id = self.env['stock.picking.type'].browse(vals.get('picking_type_id', False))
			transfer_id = self.env['stock.internal.transfer'].browse(vals.get('transfer_id', False))
			if picking_type_id and picking_type_id.code == 'outgoing' and not context.get('action_create_do_from_sample') and not transfer_id:
				vals['name'] = 'Draft'

		# if context.get('sale_order_id'):
		# 	sale_id = self.env['sale.order'].browse(context.get('sale_order_id'))

		# # if sale_id:
		# sequence = self.env.company.delivery_order_invoice_sequence_id.code
		# sequence_taiwan = self.env.company.delivery_order_invoice_taiwan_sequence_id.code
		# sequence_india = self.env.company.delivery_order_invoice_india_sequence_id.code
		# user = ""
		# if sale_id:
		# 	if sale_id.user_confirm_id:
		# 		user = sale_id.user_confirm_id
		# if not sale_id:
		# 	user = self.env.user

		# if sequence and not user.cs_invoice_sequence_type:
		# 	name = self.env['ir.sequence'].next_by_code(sequence) or '/'
		# 	vals['name'] = name
		# if sequence_taiwan and user.cs_invoice_sequence_type == 'invoice taiwan':
		# 	name = self.env['ir.sequence'].next_by_code(sequence_taiwan) or '/'
		# 	vals['name'] = name
		# if sequence_india and user.cs_invoice_sequence_type == 'invoice india':
		# 	name = self.env['ir.sequence'].next_by_code(sequence_india) or '/'
		# 	vals['name'] = name
		return super().create(vals_list)

	def create_bill_from_receipt(self):
		for picking in self:
			if picking.is_iconnexion or picking.is_mccoy:
				if self._context.get('action_create_bill_from_receipt'):
					account_move_obj = self.env['account.move'].search([('receipt_id', '=', picking.id)])
					if account_move_obj:
						raise ValidationError("Cannot Create an Bill! the bill has already been created.")
					if picking.purchase_id:
						invoice_lines = []
						for move in picking.move_ids_without_package:
							if move.purchase_line_id and move.purchase_line_id.order_id and not move.quantity_done <= 0:
								invoice_line_vals = ({
									'display_type': move.purchase_line_id.display_type,
									'sequence': move.purchase_line_id.sequence,
									'name': '%s(%s): %s' % (move.purchase_line_id.order_id.name, picking.name, move.purchase_line_id.name),
									'product_id': move.purchase_line_id.product_id.id,
									'product_uom_id': move.purchase_line_id.product_uom.id,
									'quantity': move.quantity_done,
									'price_unit': move.purchase_line_id.price_unit,
									'tax_ids': [(6, 0, move.purchase_line_id.taxes_id.ids)],
									'analytic_account_id': move.purchase_line_id.account_analytic_id.id,
									'analytic_tag_ids': [(6, 0, move.purchase_line_id.analytic_tag_ids.ids)],
									'purchase_line_id': move.purchase_line_id.id,
								})
								invoice_lines.append((0, 0, invoice_line_vals))
						journal = self.env['account.move'].with_context(default_move_type='in_invoice')._get_default_journal()
						if not journal:
							raise UserError(_('Please define an accounting purchases journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
						invoice_vals = {
							'ref': picking.purchase_id.partner_ref or '',
							'move_type': 'in_invoice',
							'narration': picking.purchase_id.notes,
							'currency_id': picking.purchase_id.currency_id.id,
							'invoice_user_id': picking.purchase_id.user_id and picking.purchase_id.user_id.id,
							'partner_id': picking.purchase_id.partner_id.id,
							'fiscal_position_id': (picking.purchase_id.fiscal_position_id or picking.purchase_id.fiscal_position_id.get_fiscal_position(picking.purchase_id.partner_id.id)).id,
							'payment_reference': picking.purchase_id.partner_ref or '',
							'partner_bank_id': picking.purchase_id.partner_id.bank_ids[:1].id,
							'invoice_origin': picking.purchase_id.name,
							'invoice_payment_term_id': picking.purchase_id.payment_term_id.id,
							'invoice_line_ids': invoice_lines,
							'company_id': picking.purchase_id.company_id.id,
							'receipt_id': picking.id,
						}
						invoice = self.env['account.move'].create(invoice_vals)
						if invoice:
							picking.vendor_bill_id = invoice.id
							return {
								'name': _('Vendor Bill'),
								'view_mode': 'form',
								'res_model': 'account.move',
								'views': [(self.env.ref('account.view_move_form').id, 'form')],
								'type': 'ir.actions.act_window',
								'res_id': invoice.id,
							}
					else:
						raise ValidationError("Cannot Create a Bill!")

	def create_invoice_from_delivery_order(self):
		for picking in self:
			if picking.is_iconnexion or picking.is_mccoy:
				if self._context.get('action_create_invoice_from_do'):
					account_move_obj = self.env['account.move'].search([('delivery_order_id', '=', picking.id)])
					if account_move_obj:
						raise ValidationError("Cannot Create an Invoice! the invoice has already been created.")
					if picking.sale_id:
						invoice_lines = []
						for move in picking.move_ids_without_package:
							if move.sale_line_id and move.sale_line_id.order_id and not move.quantity_done <= 0:
								invoice_line_vals = ({
									'display_type': move.sale_line_id.display_type,
									'sequence': move.sale_line_id.sequence,
									'name': move.sale_line_id.name,
									'product_id': move.sale_line_id.product_id.id,
									'product_uom_id': move.sale_line_id.product_uom.id,
									'quantity': move.quantity_done,
									'discount': move.sale_line_id.discount,
									'price_unit': move.sale_line_id.price_unit,
									'tax_ids': [(6, 0, move.sale_line_id.tax_id.ids)],
									'analytic_account_id': move.sale_line_id.order_id.analytic_account_id.id,
									'analytic_tag_ids': [(6, 0, move.sale_line_id.analytic_tag_ids.ids)],
									'sale_line_ids': [(4, move.sale_line_id.id)],
								})
								invoice_lines.append((0, 0, invoice_line_vals))
						journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
						if not journal:
							raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
						invoice_vals = {
							'ref': picking.sale_id.client_order_ref or '',
							'move_type': 'out_invoice',
							'narration': picking.sale_id.note,
							'currency_id': picking.sale_id.pricelist_id.currency_id.id,
							'campaign_id': picking.sale_id.campaign_id.id,
							'medium_id': picking.sale_id.medium_id.id,
							'source_id': picking.sale_id.source_id.id,
							'invoice_user_id': picking.sale_id.user_id and picking.sale_id.user_id.id,
							'team_id': picking.sale_id.team_id.id,
							'partner_id': picking.sale_id.partner_invoice_id.id,
							'partner_shipping_id': picking.sale_id.partner_shipping_id.id,
							'fiscal_position_id': (picking.sale_id.fiscal_position_id or picking.sale_id.fiscal_position_id.get_fiscal_position(picking.sale_id.partner_invoice_id.id)).id,
							'partner_bank_id': picking.sale_id.company_id.partner_id.bank_ids[:1].id,
							'journal_id': journal.id,  # company comes from the journal
							'invoice_origin': picking.sale_id.name,
							'invoice_payment_term_id': picking.sale_id.payment_term_id.id,
							'payment_reference': picking.sale_id.reference,
							'transaction_ids': [(6, 0, picking.sale_id.transaction_ids.ids)],
							'invoice_line_ids': invoice_lines,
							'company_id': picking.sale_id.company_id.id,
							'delivery_method_id': picking.sale_id.carrier_id.id,
							'freight_terms_id': picking.sale_id.freight_terms_id.id,
							'delivery_order_id': picking.id,
						}
						invoice = self.env['account.move'].create(invoice_vals)
						if 'DO' in picking.name and not ('DOT' in picking.name or 'DOI' in picking.name):
							invoice.write({
								'name': picking.name.replace('DO','INV'),
							})
						elif 'DOT' in picking.name:
							invoice.write({
								'name': picking.name.replace('DOT','INT'),
							})
						elif 'DOI' in picking.name:
							invoice.write({
								'name': picking.name.replace('DOI','INI'),
							})

						if invoice:
							return {
								'name': _('Customer Invoice'),
								'view_mode': 'form',
								'res_model': 'account.move',
								'views': [(self.env.ref('account.view_move_form').id, 'form')],
								'type': 'ir.actions.act_window',
								'res_id': invoice.id,
							}
					else:
						raise ValidationError("Cannot Create an Invoice!")

	def run_scheduler_unreserve(self):
		stock_picking_obj = self.env['stock.picking'].search([('is_iconnexion', '=', True),('state', '=', 'assigned'), ('picking_type_code', '=', 'outgoing')])
		for picking in stock_picking_obj:
			for moves in picking.move_ids_without_package:
				if moves.state in  ['assigned', 'partially_available']:
					moves.picking_id.do_unreserve()
		return True

	@api.depends('sale_id','date_cogs','date_cogs2')
	def _compute_date_cogs(self):
		for picking in self:
			picking.date_cogs = picking.sale_id.date_order
			if picking.date_cogs2:
				picking.date_cogs = picking.date_cogs2

	def _set_cogs_date(self):
		for picking in self:            
			picking.write({'date_cogs2': picking.date_cogs})
			
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

	@api.constrains('sale_id')
	def add_freight_terms_from_sale_order(self):
		for picking in self:
			if picking.is_iconnexion or picking.is_mccoy:
				if picking.sale_id.freight_terms_id:
					picking.freight_terms_id = picking.sale_id.freight_terms_id.id


	def _action_done(self):
		"""Call `_action_done` on the `stock.move` of the `stock.picking` in `self`.
		This method makes sure every `stock.move.line` is linked to a `stock.move` by either
		linking them to an existing one or a newly created one.

		If the context key `cancel_backorder` is present, backorders won't be created.

		:return: True
		:rtype: bool
		"""
		res = super(StockPicking, self)._action_done()
		# for picking in self:
		if self.date_cogs:
			self.write({'date_done': self.date_cogs, 'priority': '0'})
		self.write({'state': 'done'})

		return True
	

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    is_sample_request_type = fields.Boolean(string="Sample Request Type", default=False)


class BufferStock(models.Model):
	_name = 'buffer.stock'
	_description = 'Buffer Stock'
	_order = 'product_id, id'

	product_id = fields.Many2one('product.product', string='Product')
	quantity = fields.Float(string='Quantity')
	stock_used = fields.Float(string='Stock Used')
	stock_move_line_id = fields.Many2one('stock.move.line', string='Stock Move Line')
	buffer_stock_lines = fields.One2many('buffer.stock.line', 'buffer_stock_id', string="Buffer Stock Lines")
	


class BufferStockLine(models.Model):
	_name = 'buffer.stock.line'
	_description = 'Buffer Stock Line'
	_order = 'product_id, id'
	
	buffer_stock_id = fields.Many2one('buffer.stock', string="Buffer Stock", required=True, ondelete="cascade")
	product_id = fields.Many2one('product.product', string='Product')
	quantity = fields.Float(string='Quantity')
	stock_used = fields.Float(string='Stock Used')
	sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
	purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')

	def name_get(self):
		res = []
		for record in self:
			name = '%s - %s' % (record.product_id.name ,record.stock_used)
			res.append((record.id, name))
		return res
