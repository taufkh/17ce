from odoo import fields, models, tools

class IconSalesHistory(models.Model):
	_name = "icon.sales.history"
	_description = "Sales History"
	_auto = False
	_rec_name = 'order_id'

	order_id = fields.Many2one('sale.order', string="Sale Order", readonly=True)
	product_id = fields.Many2one('product.product', string="Product", readonly=True)
	product_tmpl_id = fields.Many2one('product.template', string="Product Template", readonly=True)
	currency_id = fields.Many2one('res.currency', string="Currency", readonly=True)
	partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
	price_unit = fields.Float('Unit Price', readonly=True)
	price_subtotal = fields.Float('Amount', readonly=True)
	qty = fields.Float('Qty', readonly=True)
	user_id = fields.Many2one('res.users', string="Salesperson", readonly=True)
	date = fields.Datetime('Date', readonly=True)

	def _select(self):
		select_str = """
			 SELECT
					sol.id as id,
					sol.order_id as order_id,
					sol.product_id as product_id,
					pp.product_tmpl_id as product_tmpl_id,
					so.currency_id as currency_id,
					so.partner_id as partner_id,
					sol.price_unit as price_unit,
					sol.price_subtotal as price_subtotal,
					sol.product_uom_qty as qty,
					so.user_id as user_id,
					so.date_order as date
		"""
		return select_str    

	def _from(self):
		from_str = """
			FROM sale_order_line sol
			LEFT JOIN sale_order as so ON so.id = sol.order_id
			LEFT JOIN product_product as pp ON pp.id = sol.product_id
		"""
		return from_str

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE view %s as
			  %s
			  
			  %s
		""" % (self._table, self._select(), self._from()))


from odoo import api, fields, models
class icon_old_sales_history(models.Model):
	_name = 'icon.old.sales.history'
	_description = 'Contains out of system old sales history'
	_rec_name = 'product_id'

	@api.depends('price_unit', 'qty')
	def _compute_subtotal(self):
		for rec in self:
			rec.price_subtotal = rec.qty * rec.price_unit

	@api.depends('cost_price', 'qty')
	def _compute_subtotal2(self):
		for rec in self:
			rec.cost_price_total = rec.qty * rec.cost_price

	product_id = fields.Many2one('product.product', string="Product", readonly=False)
	product_tmpl_id = fields.Many2one('product.template', related="product_id.product_tmpl_id", store=True)
	currency_id = fields.Many2one('res.currency', string="Currency", readonly=False)
	partner_id = fields.Many2one('res.partner', string="Customer", readonly=False)
	partner2_id = fields.Many2one('res.partner', string="Vendor", readonly=False)
	price_unit = fields.Float('Unit Price',digits='Product Price', readonly=False)
	price_subtotal = fields.Float('Amount',digits='Product Price', readonly=True, compute="_compute_subtotal", store=True)
	qty = fields.Float('Qty', readonly=False)
	date = fields.Datetime('Date', readonly=False)  
	type = fields.Selection([('quote','Quotation'),('sales','Sales')],string="Type")  
	user_id = fields.Many2one('res.users', string="Salesperson", readonly=False)
	remark = fields.Char('Remark')
	brands = fields.Char('Brand')
	customer_po = fields.Char('Customer PO')
	cpn = fields.Char('CPN')
	uom_char = fields.Char('UOM')
	icpo_no  = fields.Char('ICPO No')
	inv =  fields.Char('INV')
	inv_date = fields.Date('INV Date', readonly=False)  
	cost_price = fields.Float('Cost Price', readonly=False)
	cost_price_total = fields.Float('Costprice Total', readonly=True, compute="_compute_subtotal2", store=True)
	company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company.id)

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		context = self._context
		if self._context.get('disable_search'):   
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
				return super(icon_old_sales_history, self).search(args, offset=offset, limit=limit, order=order, count=count)
			
			report_to_user_ids = self.env.user.report_to_user_ids
			r_ids = [ n.id for n in report_to_user_ids]
			user_domain = [self.env.user.id]
			if r_ids:
				
				for r in r_ids:
					user_domain.append(r)
			args += [('partner_id.user_id','in',user_domain)]
		res = super(icon_old_sales_history, self).search(args, offset=offset, limit=limit, order=order, count=count)
		return res

	@api.model
	def _get_view(self, view_id=None, view_type='form', **options):
		"""
		Overrides orm field_view_get.
		@return: Dictionary of Fields, arch and toolbar.
		"""

		arch, view = super()._get_view(view_id, view_type, **options)
		# export_xlsx="0"
		if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_user'):			
			export_true = """<tree string="Sales" export_xlsx="1">"""
			arch = arch.replace(str("""<tree string="Sales" export_xlsx="0">"""),export_true )
		
		return arch, view

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		if self._context.get('disable_search'):  
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
				return super(icon_old_sales_history, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
  
			report_to_user_ids = self.env.user.report_to_user_ids
			r_ids = [ n.id for n in report_to_user_ids]
			user_domain = [self.env.user.id]
			if r_ids:                
				for r in r_ids:
					user_domain.append(r)
			domain += [('partner_id.user_id','in',user_domain)]

		res = super(icon_old_sales_history, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
		return res

class icon_old_quote_history(models.Model):
	_name = 'icon.old.quote.history'
	_description = 'Contains out of system old quote history'
	_rec_name = 'product_id'

	@api.depends('price_unit', 'qty')
	def _compute_subtotal(self):
		for rec in self:
			self.price_subtotal = self.qty * self.price_unit

	product_id = fields.Many2one('product.product', string="Product", readonly=False)
	product_tmpl_id = fields.Many2one('product.template', related="product_id.product_tmpl_id", store=True)
	currency_id = fields.Many2one('res.currency', string="Currency", readonly=False)
	partner_id = fields.Many2one('res.partner', string="Customer", readonly=False)
	price_unit = fields.Float('U/P (USD)',digits='Product Price', readonly=False)
	price_subtotal = fields.Float('Amount', readonly=True,digits='Product Price', compute="_compute_subtotal", store=True)
	qty = fields.Float('Qty', readonly=False)
	date = fields.Datetime('Date', readonly=False)  
	type = fields.Selection([('quote','Quotation'),('sales','Sales')],string="Type") 
	user_id = fields.Many2one('res.users', string="Salesperson", readonly=False)
	remark = fields.Char('Remark')
	project_name = fields.Char('Project Name')
	eau = fields.Float('EAU')
	moq = fields.Float('MOQ')
	spq = fields.Float('SPQ')
	company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company.id)

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		context = self._context
		if self._context.get('disable_search'):   
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
				return super(icon_old_quote_history, self).search(args, offset=offset, limit=limit, order=order, count=count)
			
			report_to_user_ids = self.env.user.report_to_user_ids
			r_ids = [ n.id for n in report_to_user_ids]
			user_domain = [self.env.user.id]
			if r_ids:
				
				for r in r_ids:
					user_domain.append(r)
			args += [('partner_id.user_id','in',user_domain)]
		res = super(icon_old_quote_history, self).search(args, offset=offset, limit=limit, order=order, count=count)
		return arch, view

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
		if self._context.get('disable_search'):  
			if self.user_has_groups('iconnexion_custom.group_iconnexion_sales_hod'):
				return super(icon_old_quote_history, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
  
			report_to_user_ids = self.env.user.report_to_user_ids
			r_ids = [ n.id for n in report_to_user_ids]
			user_domain = [self.env.user.id]
			if r_ids:                
				for r in r_ids:
					user_domain.append(r)
			domain += [('partner_id.user_id','in',user_domain)]

		res = super(icon_old_quote_history, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
		return res