
import json
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall
from re import split as regex_split

from dateutil import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_repr, float_round
from odoo.tools.misc import format_date

PROCUREMENT_PRIORITIES = [('0', 'Normal'), ('1', 'Urgent')]


class StockMove(models.Model):
	_inherit = "stock.move"

	def _get_companies_from_config(self, config_key):
		companies = self.env['res.company']
		raw_refs = (self.env['ir.config_parameter'].sudo().get_param(config_key) or '').strip()
		if not raw_refs:
			return companies
		for token in [x.strip() for x in raw_refs.split(',') if x.strip()]:
			if token.isdigit():
				companies |= self.env['res.company'].browse(int(token))
			else:
				company = self.env.ref(token, raise_if_not_found=False)
				if company and company._name == 'res.company':
					companies |= company
		return companies.exists()


	@api.depends('product_id', 'picking_type_id', 'picking_id', 'quantity', 'priority', 'state', 'product_uom_qty')
	def _compute_forecast_information(self):
		""" Compute forecasted information of the related product by warehouse."""
		self.forecast_availability = False
		self.forecast_expected_date = False
		self = self.with_user(SUPERUSER_ID)
		not_product_moves = self.filtered(lambda move: move.product_id.type != 'product')
		for move in not_product_moves:
			move.forecast_availability = move.product_qty
		outgoing_unreserved_moves_per_warehouse = defaultdict(lambda: self.env['stock.move'])
		for move in (self - not_product_moves):
			picking_type = move.picking_type_id or move.picking_id.picking_type_id
			is_unreserved = move.state in ('waiting', 'confirmed', 'partially_available')
			if picking_type.code in self._consuming_picking_types() and is_unreserved:
				outgoing_unreserved_moves_per_warehouse[picking_type.warehouse_id] |= move
			elif picking_type.code in self._consuming_picking_types():
				move.forecast_availability = move.quantity

		for warehouse, moves in outgoing_unreserved_moves_per_warehouse.items():
			product_variant_ids = moves.product_id.ids
			wh_location_ids = [loc['id'] for loc in self.env['stock.location'].search_read(
				[('id', 'child_of', warehouse.view_location_id.id)],
				['id'],
			)]
			forecast_lines = self.env['report.stock.report_product_product_replenishment']\
				._get_report_lines(None, product_variant_ids, wh_location_ids)
			for move in moves:
				lines = [l for l in forecast_lines if l["move_out"] == move._origin and l["replenishment_filled"] is True]
				if lines:
					move.forecast_availability = sum(m['quantity'] for m in lines)
					move_ins_lines = list(filter(lambda report_line: report_line['move_in'], lines))
					if move_ins_lines:
						expected_date = max(m['move_in'].date for m in move_ins_lines)
						move.forecast_expected_date = expected_date

	def _trigger_assign(self):
		""" Check for and trigger action_assign for confirmed/partially_available moves related to done moves.
			Disable auto reservation if user configured to do so.
		"""
		if not self or self.env['ir.config_parameter'].sudo().get_param('stock.picking_no_auto_reserve'):
			return

		no_reserve_companies = self._get_companies_from_config('iconnexion_mccoy_custom.no_auto_reserve_company_refs')
		if no_reserve_companies and any(move.company_id in no_reserve_companies for move in self):
			return

		domains = []
		for move in self:
			domains.append([('product_id', '=', move.product_id.id), ('location_id', '=', move.location_dest_id.id)])
		static_domain = [('state', 'in', ['confirmed', 'partially_available']), ('procure_method', '=', 'make_to_stock')]
		moves_to_reserve = self.env['stock.move'].search(expression.AND([static_domain, expression.OR(domains)]),
															order='priority desc, date asc, id asc')
		moves_to_reserve._action_assign()

	# def _action_assign(self):
	# 	""" Reserve stock moves by creating their stock move lines. A stock move is
	# 	considered reserved once the sum of `product_qty` for all its move lines is
	# 	equal to its `product_qty`. If it is less, the stock move is considered
	# 	partially available.
	# 	"""
	# 	assigned_moves = self.env['stock.move']
	# 	partially_available_moves = self.env['stock.move']
	# 	# Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
	# 	# cache invalidation when actually reserving the move.
	# 	reserved_availability = {move: move.reserved_availability for move in self}
	# 	roundings = {move: move.product_id.uom_id.rounding for move in self}
	# 	move_line_vals_list = []
	# 	for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
	# 		rounding = roundings[move]
	# 		missing_reserved_uom_quantity = move.product_uom_qty - reserved_availability[move]
	# 		missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')
	# 		if move._should_bypass_reservation():
	# 			# create the move line(s) but do not impact quants
	# 			if move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
	# 				for i in range(0, int(missing_reserved_quantity)):
	# 					move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
	# 			else:
	# 				to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
	# 														ml.location_id == move.location_id and
	# 														ml.location_dest_id == move.location_dest_id and
	# 														ml.picking_id == move.picking_id and
	# 														not ml.lot_id and
	# 														not ml.package_id and
	# 														not ml.owner_id)
	# 				if to_update:
	# 					to_update[0].product_uom_qty += missing_reserved_uom_quantity
	# 				else:
	# 					move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
	# 			assigned_moves |= move
	# 		else:
	# 			if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
	# 				assigned_moves |= move
	# 			elif not move.move_orig_ids:
	# 				if move.procure_method == 'make_to_order':
	# 					continue
	# 				# If we don't need any quantity, consider the move assigned.
	# 				need = missing_reserved_quantity
	# 				if float_is_zero(need, precision_rounding=rounding):
	# 					assigned_moves |= move
	# 					continue
	# 				# Reserve new quants and create move lines accordingly.
	# 				forced_package_id = move.package_level_id.package_id or None
	# 				lot_id = []
	# 				if self._context.get('force_action_assign'):
	# 					if move.sale_line_id:					

	# 						#'sale_order_line_purchase_order_line_rel' ,'sale_order_line_id','purchase_order_line_id',

	# 						self._cr.execute("""SELECT sml.lot_id from stock_move_line sml inner join stock_move sm on sm.id = sml.move_id 
	# 											inner join purchase_order_line pol on pol.id = sm.purchase_line_id inner join sale_order_line_purchase_order_line_rel solpol on solpol.sale_order_line_id = pol.id 
	# 											inner join sale_order_line sol2 on sol2.id = solpol.purchase_order_line_id inner join stock_move sm2 on sm2.sale_line_id = sol2.id where sm2.id = %s """, (move.id,))
	# 						# self._cr.fetchall():
	# 						res = self._cr.fetchall()
	# 						for r in res:
	# 							lot_id.append(r[0])

	# 				available_quantity = move._get_available_quantity(move.location_id, package_id=forced_package_id)
	# 				if lot_id:
	# 					lots = self.env['stock.production.lot'].browse(lot_id[0])
	# 					available_quantity = move._get_available_quantity(move.location_id,lot_id=lots, package_id=forced_package_id)
	# 				if available_quantity <= 0:
	# 					continue
	# 				if lot_id:
	# 					lots = self.env['stock.production.lot'].browse(lot_id)
	# 					for lot_icon in lots:
	# 						#force availability
	# 						available_quantity = move._get_available_quantity(move.location_id,lot_id=lot_icon, package_id=forced_package_id)
	# 						taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, lot_id=lot_icon, package_id=forced_package_id, strict=False)						
	# 						#taken multiple lots
	# 						if float_is_zero(taken_quantity, precision_rounding=rounding):
	# 							continue
	# 						# print (error)
	# 						if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
	# 							assigned_moves |= move
	# 						else:
	# 							partially_available_moves |= move

	# 				else:
	# 					#else when not lots 12 2022
	# 					if self._context.get('force_action_assign'):
	# 						continue
	# 					taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, package_id=forced_package_id, strict=False)
					
	# 				#default coding
	# 					if float_is_zero(taken_quantity, precision_rounding=rounding):
	# 						continue

	# 					if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
	# 						assigned_moves |= move
	# 					else:
	# 						partially_available_moves |= move
	# 			else:
	# 				# Check what our parents brought and what our siblings took in order to
	# 				# determine what we can distribute.
	# 				# `qty_done` is in `ml.product_uom_id` and, as we will later increase
	# 				# the reserved quantity on the quants, convert it here in
	# 				# `product_id.uom_id` (the UOM of the quants is the UOM of the product).
	# 				move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
	# 				keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

	# 				def _keys_in_sorted(ml):
	# 					return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

	# 				grouped_move_lines_in = {}
	# 				for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
	# 					qty_done = 0
	# 					for ml in g:
	# 						qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
	# 					grouped_move_lines_in[k] = qty_done
	# 				move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move)\
	# 					.filtered(lambda m: m.state in ['done'])\
	# 					.mapped('move_line_ids')
	# 				# As we defer the write on the stock.move's state at the end of the loop, there
	# 				# could be moves to consider in what our siblings already took.
	# 				moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
	# 				moves_out_siblings_to_consider = moves_out_siblings & (assigned_moves + partially_available_moves)
	# 				reserved_moves_out_siblings = moves_out_siblings.filtered(lambda m: m.state in ['partially_available', 'assigned'])
	# 				move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped('move_line_ids')
	# 				keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

	# 				def _keys_out_sorted(ml):
	# 					return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

	# 				grouped_move_lines_out = {}
	# 				for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
	# 					qty_done = 0
	# 					for ml in g:
	# 						qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
	# 					grouped_move_lines_out[k] = qty_done
	# 				for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
	# 					grouped_move_lines_out[k] = sum(self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
	# 				available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for key in grouped_move_lines_in.keys()}
	# 				# pop key if the quantity available amount to 0
	# 				available_move_lines = dict((k, v) for k, v in available_move_lines.items() if v)

	# 				if not available_move_lines:
	# 					continue
	# 				for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
	# 					if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
	# 						available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.product_qty
	# 				for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
	# 					need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
	# 					# `quantity` is what is brought by chained done move lines. We double check
	# 					# here this quantity is available on the quants themselves. If not, this
	# 					# could be the result of an inventory adjustment that removed totally of
	# 					# partially `quantity`. When this happens, we chose to reserve the maximum
	# 					# still available. This situation could not happen on MTS move, because in
	# 					# this case `quantity` is directly the quantity on the quants themselves.
	# 					available_quantity = move._get_available_quantity(location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
	# 					if float_is_zero(available_quantity, precision_rounding=rounding):
	# 						continue
	# 					taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)
	# 					if float_is_zero(taken_quantity, precision_rounding=rounding):
	# 						continue
	# 					if float_is_zero(need - taken_quantity, precision_rounding=rounding):
	# 						assigned_moves |= move
	# 						break
	# 					partially_available_moves |= move
	# 		if move.product_id.tracking == 'serial':
	# 			move.next_serial_count = move.product_uom_qty


	# 	self.env['stock.move.line'].create(move_line_vals_list)
	# 	partially_available_moves.write({'state': 'partially_available'})
	# 	assigned_moves.write({'state': 'assigned'})
	# 	self.mapped('picking_id')._check_entire_pack()


	def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
		self.ensure_one()
		AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

		move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
		if move_lines:
			date = self._context.get('force_period_date', fields.Date.context_today(self))
			picking_date = self.picking_id.scheduled_date.date() if self.picking_id.scheduled_date else date
			if self.picking_id.sale_id:
				if self.picking_id.date_cogs:
					picking_date = self.picking_id.date_cogs
				
			new_account_move = AccountMove.sudo().create({
				'journal_id': journal_id,
				'line_ids': move_lines,
				'date': picking_date,
				'ref': description,
				'stock_move_id': self.id,
				'stock_valuation_layer_ids': [(6, None, [svl_id])],
				'move_type': 'entry',
			})
			new_account_move._post()

class StockMoveLine(models.Model):
	_inherit= 'stock.move.line'
		
	stock_used = fields.Float(string="Stock Used", compute='_compute_stock_used')
	buffer_stocks = fields.Float(string="Buffer Stocks", compute='_compute_buffer_stock')
	buffer_stocks_rel = fields.Float(string="Buffer Stocks (Related)", related="buffer_stocks", store=True)
	icon_factory_reschedule_date = fields.Date(string='Factory Reschedule Date', compute='_compute_factory_date')
	warehouse_label_code = fields.Char(string="Label Code", compute='_compute_label_code')
	
	def _compute_label_code(self):
		for line in self:
			parts = []

			if line.picking_id and line.picking_id.sale_id and line.picking_id.sale_id.client_order_ref:
				parts.append(line.picking_id.sale_id.client_order_ref)
			else:
				parts.append("")

			if line.move_id and line.move_id.name:
				parts.append(line.move_id.name)
			else:
				parts.append("")

			if line.product_id and line.product_id.name:
				parts.append(line.product_id.name)
			else:
				parts.append("")

			if line.qty_done:
				parts.append(str(line.qty_done))
			else:
				parts.append("")

			if line.dc:
				parts.append(line.dc)
			else:
				parts.append("")

			if line.lot_id and line.lot_id.name:
				parts.append(line.lot_id.name)
			else:
				parts.append("")

			if line.coo:
				parts.append(line.coo)
			else:
				parts.append("")

			if line.product_id and line.product_id.product_brand_id and line.product_id.product_brand_id.name:
				parts.append(line.product_id.product_brand_id.name)
			else:
				parts.append("")

			combined_value = ", ".join(parts)
			line.warehouse_label_code = combined_value

	def _compute_factory_date(self):
		for i in self:
			i.icon_factory_reschedule_date = i.move_id.purchase_line_id.icon_factory_reschedule_date


	def name_get(self):
		res = []
		for record in self:
			name = '%s - %s) %s' % (record.origin ,record.serial_numbers, record.product_id.name)
			res.append((record.id, name))
		return res
	

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('origin', operator, name), ('product_id.name', operator, name)]
		stock_lines = self.search(domain + args, limit=limit)
		return stock_lines.name_get()


	def _compute_buffer_stock(self):
		for i in self:
			i.buffer_stocks = i.qty_done - i.stock_used
			
	def _compute_stock_used(self):
		for i in self:
			stocks = 0
			buffer_stock_line = self.env['buffer.stock'].search([('stock_move_line_id', '=', i.id)])
			for buffer_line in buffer_stock_line:
				stocks = buffer_line.stock_used

			i.stock_used = stocks

class StockValuationLayer(models.Model):
	_inherit = "stock.valuation.layer"

	date_cogs = fields.Datetime(
		"Date Transfer", readonly=False, copy=False,
		help="Date Valuation",compute='_compute_date_cogs', index=True, store=True)
	is_locked = fields.Boolean('is Locked', default=False)
	show_mark_as_todo = fields.Boolean('Show Mark as Todo', default=False)
	show_check_availability = fields.Boolean('Show Check Availability', default=False)
	show_validate = fields.Boolean('Show Validate', default=False)
	show_lots_text = fields.Boolean('Show Lots Text', default=False)
	immediate_transfer = fields.Boolean('Immediate Transfer', default=False)
	picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], string="Type", readonly=True)
	hide_picking_type = fields.Boolean('Hide Picking Type', default=False)

	@api.depends('company_id','product_id','description','date_cogs')
	def _compute_date_cogs(self):
		for valuation in self:
			# company_name = move.company_id.name
			if valuation.stock_move_id:
				if valuation.stock_move_id.picking_id:
					if valuation.stock_move_id.picking_id.date_done:
						valuation.date_cogs = valuation.stock_move_id.picking_id.date_done

					if valuation.stock_move_id.picking_id.date_cogs:
						valuation.date_cogs = valuation.stock_move_id.picking_id.date_cogs
