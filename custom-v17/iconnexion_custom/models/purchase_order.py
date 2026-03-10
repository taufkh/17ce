from odoo import api, fields, models, tools, _, SUPERUSER_ID
from dateutil.relativedelta import relativedelta,FR
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	icon_related_so_ids = fields.Many2many('sale.order', 'icon_sale_purchase_rel' ,'sale_id','purchase_id', string="SO Number")
	contact_id = fields.Many2one('res.partner','Contact')
	
	@api.constrains('amount_total')
	def notify_po_value(self):
		notifications = []
		for po in self:
			if po.amount_total < 300:
				message = _('PO Value is Under 300! \n (%s) ') % (po.name)
				notifications.append([                
					(self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
					{'type': 'simple_notification', 'title': _('Warning Message'), 'message': message, 'sticky': True, 'warning': True}])
				if self.env.user != po.user_id:
					notifications.append([
					(self._cr.dbname, 'res.partner', self.user_id.partner_id.id),
					{'type': 'simple_notification', 'title': _('Warning Message'), 'message': message, 'sticky': True, 'warning': True}])
		self.env['bus.bus'].sendmany(notifications)

	def button_confirm(self):
		res = super(PurchaseOrder, self).button_confirm()
		for line in self.order_line:
			if line.product_qty < line.icon_so_line_qty:
				raise UserError('Please Check SO Quantity before confirming !')
		return res

	def button_confirm_bypass(self):
		for order in self:
			if order.state not in ['draft', 'sent']:
				continue
			order._add_supplier_to_product()
            # Deal with double validation process
			if order._approval_allowed():
				order.button_approve()
			else:
				order.write({'state': 'to approve'})
			if order.partner_id not in order.message_partner_ids:
				order.message_subscribe([order.partner_id.id])
		return True


	def _approval_allowed(self):
		"""Returns whether the order qualifies to be approved by the current user"""
		self.ensure_one()
		return (
			self.company_id.po_double_validation == 'one_step'
			or (self.company_id.po_double_validation == 'two_step'
				and self.amount_total < self.env.company.currency_id._convert(
					self.company_id.po_double_validation_amount, self.currency_id, self.company_id,
					self.date_order or fields.Date.today()))
			or self.user_has_groups('purchase.group_purchase_manager'))

	def button_combine(self):
		if self.order_line:
			product_ids = []
			counter = 1
			quantity = 0
			for line in self.order_line:
				if line.product_id.id not in product_ids:
					product_ids.append(line.product_id.id)
			for data in product_ids:
				search_order_line = self.env['purchase.order.line'].search([('order_id','=',self.id),('product_id','=', data),('is_combine','=', True)])
				keep_id = []
				delete_ids = []
				if len(search_order_line) > 1: 
					for line in search_order_line:
						if counter == 1:
							keep_id.append(line.id)
						else:
							delete_ids.append(line.id)
						counter+=1
						quantity += line.product_qty
				keep_line = self.env['purchase.order.line'].search([('order_id','=',self.id),('id','=', keep_id)])
				keep_line.product_qty = quantity
				delete_line = self.env['purchase.order.line'].search([('order_id','=',self.id),('id','in', delete_ids)])
				delete_line.unlink()

	@api.onchange('partner_id', 'company_id')
	def onchange_icon_partner_id(self):
		# Ensures all properties and fiscal positions
		# are taken with the company of the order
		# if not defined, with_company doesn't change anything.
		self = self.with_company(self.company_id)
		if not self.partner_id:
			self.fiscal_position_id = False
			self.freight_terms = False
		else:
			self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
			self.freight_terms = self.partner_id.freight_terms
		return {}

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	icon_picking_ref_id = fields.Many2one('stock.picking', string="Picking Ref")
	icon_sale_id = fields.Many2one('sale.order', string="SO Number")
	icon_sale_ids = fields.Many2many('sale.order.line', 'sale_order_line_purchase_order_line_rel' ,'sale_order_line_id','purchase_order_line_id', string="SO Number Lines",copy=False)
	icon_sale_line_id = fields.Many2one('sale.order.line', string="SO Number Line (Primary)") #link to Sale Line 
	icon_so_qty = fields.Float(compute='_compute_so_qty', string='SO Qty', store=True, readonly=True,
								  digits='Product Unit of Measure')
	icon_so_line_qty = fields.Float(compute='_compute_so_line_qty', string='SO Quantity', digits='Product Unit of Measure') #qty of request
	icon_total_sale_current = fields.Float(compute='_compute_total_sale', string='Total Sale Price (Current)', compute_sudo=False) #qty of request
	icon_total_sale = fields.Float(compute='_compute_total_sale', string='Total Sale Price', store=True, compute_sudo=False) #qty of request
	#stock information
	icon_coo = fields.Char(compute='_stock_information',string='COO', compute_sudo=False)
	icon_date_code = fields.Char(compute='_stock_information',string='DC', compute_sudo=False)
	icon_lot_batch_1 = fields.Char(compute='_stock_information',string='Lot Batch 1', compute_sudo=False)
	icon_lot_batch_2 = fields.Char(compute='_stock_information',string='Lot Batch 2', compute_sudo=False)
	icon_l = fields.Char(compute='_stock_information',string='L', compute_sudo=False)
	icon_w = fields.Char(compute='_stock_information',string='W', compute_sudo=False)
	icon_h = fields.Char(compute='_stock_information',string='H', compute_sudo=False)
	icon_weight = fields.Float(compute='_stock_information',string='Weight', compute_sudo=False)
	icon_location = fields.Char(compute='_stock_information',string='Location', store=True, compute_sudo=False)
	icon_uid = fields.Char(compute='_stock_information',string='UID', compute_sudo=False)
	# #goods out
	icon_qty_taken = fields.Float(compute='_stock_information',string='QTY Taken',store=True, compute_sudo=False)
	icon_date_taken = fields.Date(compute='_stock_information', string='Date Taken', compute_sudo=False)
	icon_scan_date = fields.Date(compute='_stock_information', string='Scan Date', store=True, compute_sudo=False)

	icpo_request_deliver_date = fields.Date('Iconn Request Date') #ICPO request delivery date. 1 week before Customer req date
	icon_reschedule_date = fields.Date('Iconn Reschedule Date')
	icon_factory_reschedule_date = fields.Date('Factory Reschedule Date') #Factory Reschedule date
	is_combine = fields.Boolean('Combine', default=False)
	icon_delivery_history_ids = fields.One2many('icon.delivery.history','purchase_line_delivery_history_id', string="Delivery History Date")
	value_purchase_aging = fields.Float(compute='_compute_value_purchase_aging',string='Value Purchase Aging',store=True)
	# SO Reference, Supplier Name, Customer Name, Salesperson.
	icon_move_id = fields.Many2one('stock.move', string="Stock Move") 
	so_reference_id = fields.Many2one('sale.order', compute='_compute_so_reference',string='SO Reference',store=False)
	customer_name_id = fields.Many2one('res.partner',compute='_compute_so_reference',string='Customer Name',store=False)
	salesperson_id = fields.Many2one('res.users',compute='_compute_so_reference',string='Salesperson',store=False)
	customer_po_number = fields.Char(compute='_compute_so_reference',string='Customer PO Number',store=False)
	# SO Reference, Supplier Name, Customer Name, Salesperson.
	serial_numbers = fields.Integer(string='No.', compute='_compute_serial_number')
	buffer_stock = fields.Float('Buffer Stock', readonly=True, compute='_compute_buffer_stock')
	r_code = fields.Char("RC", compute='_compute_replenish_code',required=False)
	
	def _compute_replenish_code(self):		
		for i in self:
			r_code = ''
			if i.product_id:
				moqs = i.product_id.product_tmpl_id.moq_ids.filtered(lambda line: (line.product_variant_id==i.product_id or not line.product_variant_id) )
				if moqs:
					r_code = moqs[0].r_code
			i.r_code = r_code
			
	def _compute_buffer_stock(self):
		quantity = 0
		for i in self:
			stock_quant_ids = self.env['stock.quant'].search([('product_id', '=', i.product_id.id),('on_hand', '=', True)])
			for stock_quant in stock_quant_ids:
				quantity += stock_quant.available_quantity
			i.buffer_stock = quantity

	@api.depends('sequence', 'order_id')
	def _compute_serial_number(self):
		for order_line in self:
			if order_line.serial_numbers == 0:
				serial_no = 1
				for line in order_line.mapped('order_id').order_line:
					line.serial_numbers = serial_no
					serial_no += 1


	@api.depends('move_ids', 'move_ids.quantity')
	def _stock_information(self):	
		for line in self:
			icon_coo = icon_date_code = icon_lot_batch_1 = icon_lot_batch_2 = ''
			icon_l = icon_l = icon_h = icon_w = icon_weight = icon_uid = icon_date_taken = ''
			icon_location = False
			icon_qty_taken = 0
			icon_scan_date = ''
			icon_uid = ''
			no_of_carton = ''
			for move in line.move_ids:
				icon_uid += line.order_id.partner_id.customer_code or ''
				icon_qty_taken += move.quantity

				if move.state == 'cancel':
					continue
				for move_line in move.move_line_nosuggest_ids:
					icon_coo = move_line.coo
					icon_date_code = move_line.dc
					icon_date_taken = move_line.date
					icon_scan_date = move_line.write_date
					no_of_carton = chr(move.no_of_carton)
					if move_line.lot_id:
						icon_lot_batch_1 = move_line.lot_id.name
						icon_location = move_line.location_dest_id.name
					icon_l = move_line.dimension_length
					icon_w = move_line.dimension_width
					icon_h = move_line.dimension_height
					icon_weight = move_line.weight
					# move_line_nosuggest_ids
				# icon_coo = 
			icon_uid += icon_date_code or ''
			icon_uid += no_of_carton or ''
			line.icon_coo = icon_coo
			line.icon_date_code = icon_date_code
			line.icon_lot_batch_1 = icon_lot_batch_1
			line.icon_lot_batch_2 = icon_lot_batch_2
			line.icon_l = icon_l
			line.icon_w = icon_w
			line.icon_h = icon_h 
			line.icon_weight = icon_weight 
			line.icon_location = icon_location
			line.icon_qty_taken = icon_qty_taken
			line.icon_uid = icon_uid
			line.icon_date_taken = icon_date_taken
			line.icon_scan_date = icon_scan_date
			
	# @api.depends('icon_factory_reschedule_date')
	def _compute_so_reference(self):		
		for line in self:
			line.so_reference_id = False
			line.customer_name_id = False
			line.salesperson_id = False
			line.customer_po_number = ''
			if line.icon_sale_ids:
				for sale_line in line.icon_sale_ids:
					line.so_reference_id = sale_line.order_id.id
					line.customer_name_id = sale_line.order_id.partner_id.id
					line.salesperson_id = sale_line.order_id.user_id.id
					line.customer_po_number = sale_line.order_id.client_order_ref
					break
	
	# Factory Reschedule Date - {Iconn Request Date + 2 weeks}
	@api.depends('icon_factory_reschedule_date', 'icpo_request_deliver_date')
	def _compute_value_purchase_aging(self):		
		for line in self:
			if line.icon_factory_reschedule_date and line.icpo_request_deliver_date:
				line.value_purchase_aging = relativedelta(
					fields.Date.from_string(line.icon_factory_reschedule_date),(
					fields.Date.from_string(line.icpo_request_deliver_date) +relativedelta(weeks=2)) ).days 
			else: 
				line.value_purchase_aging = 0


	def _track_date_received(self, date_planned):
		self.ensure_one()
		date_delivery = datetime.strptime(date_planned, '%Y-%m-%d %H:%M:%S')
		if date_planned != self.date_planned and self.order_id.state == 'purchase':
			self.order_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
				'iconnexion_custom.track_po_line_date_received_template',
				values={'line': self, 'date_planned_start':(self.date_planned+ relativedelta(weeks=1, weekday=FR)).strftime('%Y-%m-%d %H:%M:%S'), 'date_planned': (date_delivery+ relativedelta(weeks=1, weekday=FR)).strftime('%Y-%m-%d %H:%M:%S')},
				subtype_id=self.env.ref('mail.mt_note').id
			)
		for line in self.icon_sale_ids:
			line.order_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
				'iconnexion_custom.track_po_line_date_received_template',
				values={'line': self, 'date_planned_start':(self.date_planned+ relativedelta(weeks=1, weekday=FR)).strftime('%Y-%m-%d %H:%M:%S'), 'date_planned': (date_delivery+ relativedelta(weeks=1, weekday=FR)).strftime('%Y-%m-%d %H:%M:%S')},
				subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
			)

	def action_delivery_history_wizard(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Change Delivery Date',
			'res_model': 'icon.delivery.history.wizard',
			'view_mode': 'form',
			'target': 'new',
			'context': {'active_id': self._context.get('active_id'), 'active_model': self._context.get('active_model')},
		}

	@api.depends('product_id', 'icon_sale_ids', 'order_id.state')
	def _compute_so_qty(self):
		for line in self:            
			# search all so qty link with icpo
			# icon_purchase_id
			qty = 0.0
			if self.user_has_groups('iconnexion_custom.group_iconnexion_company'):   
				for sline in line.icon_sale_ids:
					qty += sline.product_uom_qty   
			line.icon_so_qty = qty

	@api.depends('icon_sale_ids')
	def _compute_total_sale(self):
		for line in self:            
			price_total = 0.0
			line.icon_total_sale_current = line.product_qty * line.product_id.lst_price
			for sline in line.icon_sale_ids:
				price_total += sline.price_total 
			line.icon_total_sale = price_total

	def _compute_so_line_qty(self):
		for line in self:            
			qty = 0.0
			if self.user_has_groups('iconnexion_custom.group_iconnexion_company'):   
				for sline in line.icon_sale_ids:
					qty += sline.product_uom_qty 
			line.icon_so_line_qty = qty

	@api.model
	def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
		res = super()._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
		res['icon_sale_ids'] = values.get('related_sl', False)
		return res

# mt_comment #for user customer service notified_partner_ids=[0,0,14360]
		# self.env.ref('mail.mt_note').id

class IconDeliveryHistory(models.Model):
	_name = 'icon.delivery.history'
	_description = "Icon Delivery History"
	_order = 'id desc'

	purchase_line_delivery_history_id = fields.Many2one('purchase.order.line', 'PO Line')
	date = fields.Date('Date')
	change_reason = fields.Char('Reason')
