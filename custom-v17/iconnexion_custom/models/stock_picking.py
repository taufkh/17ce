from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.tools.misc import formatLang, format_date
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

class StockValuationLayer(models.Model):
	"""Stock Valuation Layer"""

	_inherit = 'stock.valuation.layer'


	# value = fields.Monetary('Total Value', readonly=True)
	value_2 = fields.Monetary("Total Value (Inverse)",compute='_compute_value',store=True)
	
	@api.depends('value')
	def _compute_value(self):
		for sv in self:
			# value_2 = 0		
			sv.value_2 = sv.value * -1
			
			
class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	sample_request_id = fields.Many2one('sample.request.form')
	sample_request_out_id = fields.Many2one('sample.request.form')
	total_packages_c = fields.Integer(string="Total Package c", compute='_compute_packages_c')

	def _compute_packages_c(self):
		for move in self:
			move.total_packages_c = 0 			
			stock_move_count = self.env['stock.move.line'].search_count([('picking_id', '=', move.id)])			
			move.total_packages_c = stock_move_count

	def _get_label_default_code_company_ids(self):
		"""Return company ids that should print product default_code on icon label."""
		param_val = self.env['ir.config_parameter'].sudo().get_param(
			'iconnexion_custom.label_use_default_code_company_ids',
			'2',
		) or ''
		company_ids = []
		for raw_id in param_val.split(','):
			raw_id = raw_id.strip()
			if not raw_id:
				continue
			try:
				company_ids.append(int(raw_id))
			except (TypeError, ValueError):
				continue
		return company_ids

	def _label_use_default_code(self):
		self.ensure_one()
		return self.company_id.id in self._get_label_default_code_company_ids()

	def _label_mfr_part_number(self, move):
		"""Return the displayable Mfr P/N for report_icon_label."""
		self.ensure_one()
		product = move.product_id
		if not product:
			return ''
		if self._label_use_default_code() and product.default_code:
			return product.default_code
		return product.name or ''
				

	@api.model
	def _get_move_line_ids_fields_to_read(self):
		""" read() on picking.move_line_ids only returns the id and the display
		name however a lot more data from stock.move.line are used by the client
		action.
		"""
		return [
			'product_id',
			'location_id',
			'location_dest_id',
			'qty_done',
			'display_name',
			'product_uom_qty',
			'product_uom_id',
			'product_barcode',
			'owner_id',
			'lot_id',
			'lot_name',
			'package_id',
			'result_package_id',
			'dummy_id',
			'product_cpn',
			'icpo_request_deliver_date',
			'is_need_picking'
		]

	def button_validate(self):
		if self.picking_type_code == 'incoming':
			for move in self.move_line_ids:
				if move.coo:
					move.product_id.product_tmpl_id._create_coo(move.coo)
				
			# self.check_lot_coa()
		return super(StockPicking, self).button_validate()

class StockMove(models.Model):
	_inherit = 'stock.move'

	iconnexion_uid = fields.Char(string="Iconnexion UID", compute='compute_iconnexion_uid', store=False)
	customer_part_number = fields.Char('CPN')
	coo = fields.Char("COO",compute='_compute_lot_icon_ids',store=True)
	dc = fields.Char("DC",compute='_compute_lot_icon_ids',store=True)
	lot_icon = fields.Char("Lot Name",compute='_compute_lot_icon_ids',store=True)
	purchase_id = fields.Many2one('purchase.order',string='Purchase Order Related', copy=False)
	icon_customer_po = fields.Char(string='Customer PO',compute='_compute_customer_po_id')
	icon_customer_id = fields.Many2one('res.partner',string='Customer',compute='_compute_customer_po_id')
	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)

	measurement_length = fields.Char('Measurement L (CM)')
	measurement_width = fields.Char('Measurement W (CM)')
	measurement_height = fields.Char('Measurement H (CM)')


	@api.depends('company_id')
	def compute_is_iconnexion(self):
		for account in self:
			company_name = account.company_id.name
			if company_name and 'iconnexion' in company_name.lower():
				account.is_iconnexion = True
			else:
				account.is_iconnexion = False

	def _compute_customer_po_id(self):
		for move in self:
			icon_customer_po = ""
			icon_customer_id = False
			if move.purchase_line_id:
				if move.purchase_line_id.icon_sale_id:
					icon_customer_po = move.purchase_line_id.icon_sale_id.client_order_ref
					if move.purchase_line_id.icon_sale_id.partner_id:
						icon_customer_id = move.purchase_line_id.icon_sale_id.partner_id.id			
				
			move.icon_customer_po = icon_customer_po
			move.icon_customer_id = icon_customer_id


	@api.depends('move_line_ids', 'move_line_ids.lot_name', 'move_line_ids.dc','move_line_ids.coo')
	def _compute_lot_icon_ids(self):
		for move in self:
			dc = ""       
			lot_icon = ""
			coo = ""
			measurement_length = ""
			measurement_width = ""
			measurement_height = ""
			for line in move.move_line_ids:
				if line.coo:
					coo = line.coo
				if line.dc:
					dc = line.dc            		
				if line.lot_name:
					lot_icon = line.lot_name

				if line.dimension_length:
					measurement_length = line.dimension_length
				if line.dimension_width:					
					measurement_width = line.dimension_width
				if line.dimension_width:					
					measurement_height = line.dimension_height

				if dc and lot_icon:
					break

			move.dc = dc
			move.lot_icon = lot_icon    
			move.coo = coo
			move.measurement_length = measurement_length
			move.measurement_width = measurement_width
			move.measurement_height = measurement_height


	# @api.depends('picking_id.partner_id','picking_id.scheduled_date','no_of_carton')
	def compute_iconnexion_uid(self):
		for move in self:
			UID = ""
			if move.picking_id:
				if move.picking_id.partner_id:
					if move.picking_id.partner_id.customer_code:
						UID += move.picking_id.partner_id.customer_code
				if move.picking_id.scheduled_date:#date_done
					# date_done = 270121  ddmmyy
					string = format_date(self.env, move.picking_id.scheduled_date, date_format='ddMMyy')
					UID += string
			if move.no_of_carton:
				UID += str(move.no_of_carton).zfill(2)
			# stock.iconnexion_uid = UID
			move.iconnexion_uid = UID

	@api.onchange('product_id')
	def onchange_product_icon(self):
		if self.product_id:
			product = self.product_id.with_context(lang=self.picking_id.partner_id.lang or self.env.user.lang)
			self.customer_part_number = product.name

from datetime import datetime, timedelta
class StockMoveLine(models.Model):
	_inherit= 'stock.move.line'

	# product_cpn = fields.Char(related='move_id.name',string="CPN")
	source_po = fields.Char(compute='_compute_product_cpn',)
	product_cpn = fields.Char(compute='_compute_product_cpn', inverse='_inverse_product_cpn')
	qty_done = fields.Float('Done', default='', digits='Product Unit of Measure', copy=False)
	icpo_no = fields.Char('PO Number', required=False)
	ic_cpn = fields.Char('CPN', required=False)
	ic_datecode = fields.Char('Date Code',  required=False)
	ic_customer = fields.Char('Customer (Legacy)',  required=False)
	icpo_request_deliver_date =  fields.Date('Iconn Request Date', compute='_compute_icpo_request',) 
	is_need_picking = fields.Boolean('Need Picking', compute='_compute_is_need_picking')
	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)
	
	dimension_length_c = fields.Char(string="Dimension (L) c", compute='_compute_dimension')
	dimension_width_c = fields.Char(string="Dimension (W) c", compute='_compute_dimension')
	dimension_height_c = fields.Char(string="Dimension (H) c", compute='_compute_dimension')
	po_number_c = fields.Char(string="PO Number c", compute='_compute_dimension')
	weight_ctn_c = fields.Float(string="Net Weight/carton", compute='_compute_dimension')
	total_gr_wt_c = fields.Float(string="Weight Ctn c", compute='_compute_dimension')
	origin = fields.Char(string="Origin", related="picking_id.origin", store=True)
	serial_numbers = fields.Integer(string='No.', compute='_compute_serial_number')
	sale_order_no = fields.Char('Sale Order', compute='_compute_sale_order_data')
	sale_order_customer = fields.Char('SO Customer', compute='_compute_sale_order_data')
	sale_order_cust_po = fields.Char('Cust. PO.', compute='_compute_sale_order_data')
	sale_order_line_product_cpn = fields.Char('SO CPN', compute='_compute_sale_order_data')
	so_order_quantity = fields.Float('SO Quantity', compute='_compute_sale_order_data')


	def _compute_sale_order_data(self):
		for record in self:
			related_orders = record.move_id.purchase_line_id.icon_sale_ids.mapped('order_id')
			related_order_line = record.move_id.purchase_line_id.icon_sale_ids
			purchase_order_line = record.move_id.purchase_line_id.icon_so_line_qty
			record.sale_order_no = '; '.join(order.name for order in related_orders) if related_orders else ''
			record.sale_order_customer = '; '.join(order.partner_id.name for order in related_orders) if related_orders else ''
			record.sale_order_cust_po = '; '.join(order.client_order_ref for order in related_orders if order.client_order_ref) if related_orders else ''
			record.sale_order_line_product_cpn = '; '.join(orderline.name for orderline in related_order_line) if related_order_line else ''
			record.so_order_quantity = purchase_order_line


	@api.depends('picking_id')
	def _compute_serial_number(self):
		for i in self:
			if i.source_po_id and i.move_id:
				if i.move_id.purchase_line_id:
					i.serial_numbers = i.move_id.purchase_line_id.serial_numbers

			if i.move_id.sale_line_id:
				i.serial_numbers = i.move_id.sale_line_id.serial_numbers
			
			else:
				if i.serial_numbers == 0:
					serial_no = 1
					for line in i.mapped('picking_id').move_line_ids_without_package:
						line.serial_numbers = serial_no
						serial_no += 1


	#check all last, stock move line yang masuk. ambil nilai nya
	def _compute_dimension(self):
		for move in self:
			lot_id = move.lot_id
			move.dimension_length_c = ""
			move.dimension_width_c = ""
			move.dimension_height_c = ""
			move.po_number_c =""
			move.weight_ctn_c = ""
			move.total_gr_wt_c = ""
			if move.picking_id.sale_id:
				move.po_number_c = move.picking_id.sale_id.client_order_ref

			if lot_id:
				stock_move_id = self.env['stock.move.line'].search([('lot_id', '=', lot_id.id),('product_id', '=', move.product_id.id),('state', '=', 'done'),('picking_code','=','incoming')],limit=1)
				
				if stock_move_id :
					move.dimension_length_c = stock_move_id.dimension_length
					move.dimension_width_c = stock_move_id.dimension_width
					move.dimension_height_c = stock_move_id.dimension_height
					# move.po_number_c = stock_move_id.picking_id.origin
					if float(stock_move_id.weight) < 1:
						move.weight_ctn_c = float(stock_move_id.weight)- 0.1
					else:	
						move.weight_ctn_c = float(stock_move_id.weight)- 0.5
					move.total_gr_wt_c = float(stock_move_id.weight)
			


	@api.depends('company_id')
	def compute_is_iconnexion(self):
		for account in self:
			company_name = account.company_id.name
			if company_name and 'iconnexion' in company_name.lower():
				account.is_iconnexion = True
			else:
				account.is_iconnexion = False

	def _compute_is_need_picking(self):
		for move in self:
			move.is_need_picking = False
			# day = '12/Oct/2013'
			dt = fields.Date.today()
			# dt = datetime.strptime(day, '%d/%b/%Y')
			start = dt - timedelta(days=dt.weekday())
			end = start + timedelta(days=6)

			if move.move_id:
				if move.move_id.purchase_line_id:
					if move.move_id.purchase_line_id.order_id:
						if move.move_id.purchase_line_id.icpo_request_deliver_date:
							dd = move.move_id.purchase_line_id.icpo_request_deliver_date
							if start <= dd <= end:								
								move.is_need_picking = True
								
	def _compute_icpo_request(self):
		for move in self:
			move.icpo_request_deliver_date = False
			if move.move_id:
				if move.move_id.purchase_line_id:
					if move.move_id.purchase_line_id.order_id:
						move.icpo_request_deliver_date = move.move_id.purchase_line_id.icpo_request_deliver_date

	@api.onchange('dimension_length')
	def onchange_dimension_length(self):
			if self.dimension_length:
				res = [int(i) for i in self.dimension_length.split() if i.isdigit()]
				if len(res) == 3:
					self.dimension_length = res[0]
					self.dimension_width = res[1]
					self.dimension_height = res[2]



	def _compute_product_cpn(self):
		for move in self:
			CPN = ""
			if move.customer_part_number:
				CPN = move.customer_part_number
			elif move.move_id:
				CPN = move.move_id.name
			move.product_cpn = CPN

	def _inverse_product_cpn(self):
		product_cpn = self[0].product_cpn
		for move in self:           
			move.write({'customer_part_number': product_cpn})

	def _action_done(self):
		""" This method is called during a move's `action_done`. It'll actually move a quant from
		the source location to the destination location, and unreserve if needed in the source
		location.

		This method is intended to be called on all the move lines of a move. This method is not
		intended to be called when editing a `done` move (that's what the override of `write` here
		is done.
		"""
		Quant = self.env['stock.quant']

		# First, we loop over all the move lines to do a preliminary check: `qty_done` should not
		# be negative and, according to the presence of a picking type or a linked inventory
		# adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
		# the line. It is mandatory in order to free the reservation and correctly apply
		# `action_done` on the next move lines.
		ml_to_delete = self.env['stock.move.line']
		ml_to_create_lot = self.env['stock.move.line']
		tracked_ml_without_lot = self.env['stock.move.line']
		for ml in self:
			# Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
			uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
			precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
			if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
				raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
								  defined on the unit of measure "%s". Please change the quantity done or the \
								  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

			qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
			
			if qty_done_float_compared > 0:
				if ml.product_id.tracking != 'none':
					picking_type_id = ml.move_id.picking_type_id
					if picking_type_id:
						if picking_type_id.use_create_lots:
							# If a picking type is linked, we may have to create a production lot on
							# the fly before assigning it to the move line if the user checked both
							# `use_create_lots` and `use_existing_lots`.
							if ml.lot_name and not ml.lot_id:
								lot = self.env['stock.production.lot'].search([
									('company_id', '=', ml.company_id.id),
									('product_id', '=', ml.product_id.id),
									('name', '=', ml.lot_name),
								])
								
								if lot:
									ml.lot_id = lot.id
								else:
									# ml_to_create_lot |= ml
									ml._create_and_assign_production_lot()
						elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
							# If the user disabled both `use_create_lots` and `use_existing_lots`
							# checkboxes on the picking type, he's allowed to enter tracked
							# products without a `lot_id`.
							continue
					elif ml.move_id.inventory_id:
						# If an inventory adjustment is linked, the user is allowed to enter
						# tracked products without a `lot_id`.
						continue

					if not ml.lot_id and ml not in ml_to_create_lot:
						tracked_ml_without_lot |= ml
			elif qty_done_float_compared < 0:
				raise UserError(_('No negative quantities allowed'))
			else:
				ml_to_delete |= ml

		if tracked_ml_without_lot:
			raise UserError(_('You need to supply a Lot/Serial Number for product: \n - ') +
							  '\n - '.join(tracked_ml_without_lot.mapped('product_id.display_name')))
		
		# ml_to_create_lot._create_and_assign_production_lot()

		ml_to_delete.unlink()

		(self - ml_to_delete)._check_company()

		# Now, we can actually move the quant.
		done_ml = self.env['stock.move.line']
		for ml in self - ml_to_delete:
			if ml.product_id.type == 'product':
				rounding = ml.product_uom_id.rounding

				# if this move line is force assigned, unreserve elsewhere if needed
				if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
					qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
					extra_qty = qty_done_product_uom - ml.product_qty
					ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
				# unreserve what's been reserved
				if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
					try:
						Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
					except UserError:
						Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

				# move what's been actually done
				quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
				available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
				if available_qty < 0 and ml.lot_id:
					# see if we can compensate the negative quants with some untracked quants
					untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
					if untracked_qty:
						taken_from_untracked_qty = min(untracked_qty, abs(quantity))
						Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
						Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
				Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
			done_ml |= ml
		# Reset the reserved quantity as we just moved it to the destination location.
		(self - ml_to_delete).with_context(bypass_reservation_update=True).write({
			'product_uom_qty': 0.00,
			'date': fields.Datetime.now(),
		})


class StockQuant(models.Model):
	_inherit = 'stock.quant'

	icpo_no = fields.Char('PO Number', required=False)
	ic_cpn = fields.Char('CPN', required=False)
	ic_datecode = fields.Char('Date Code',  required=False)
	ic_customer = fields.Char('Customer',  required=False)
	# location_id = fields.Many2one(
	# 	'stock.location', 'Location',
	# 	domain=lambda self: self._domain_location_id(),
	# 	auto_join=True, ondelete='restrict', readonly=True, required=True, index=True, check_company=True)
	# lot_id = fields.Many2one(
	# 	'stock.production.lot', 'Lot/Serial Number',
	# 	ondelete='restrict', readonly=True, check_company=True,
	# 	domain=lambda self: self._domain_lot_id())
	# product_id = fields.Many2one(
	# 	'product.product', 'Product',
	# 	domain=lambda self: self._domain_product_id(),
	# 	ondelete='restrict', readonly=True, required=True, index=True, check_company=True)
