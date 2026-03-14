# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression
from odoo.tools.translate import html_translate
import datetime

_logger = logging.getLogger(__name__)


# v16: mccoy.product.moq not available (mccoy_custom is uninstallable); class disabled
# class McCoyProductMOQ(models.Model):
# 	_inherit = "mccoy.product.moq"
# 	r_code = fields.Char("Replenishment code",required=False)
# 	price_unit = fields.Float("Price Unit", digits='Product Price',required=True)



class IconCoo(models.Model):
	_name = "icon.coo"
	_description = "Country of Origin"

	name = fields.Char("COO")

class ProductTemplate(models.Model):
	_inherit = "product.template"

	coo = fields.Char("COO (Text)", tracking=True)
	coo_id = fields.Many2one('icon.coo', string="COO Reference", tracking=True)
	class_id = fields.Many2one("product.class",'Item Class')
	#history
	icon_sales_history_ids = fields.One2many('icon.sales.history','product_tmpl_id', string="Sales History")
	old_sales_history_ids = fields.One2many('icon.old.sales.history', 'product_tmpl_id', string="Old Sales History")
	old_quote_history_ids = fields.One2many('icon.old.quote.history', 'product_tmpl_id', string="Old Quotation History")
	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)


	@api.depends('company_id')
	def compute_is_iconnexion(self):
		for lead in self:
			company_name = lead.company_id.name
			if company_name and 'iconnexion' in company_name.lower():
				lead.is_iconnexion = True
			else:
				lead.is_iconnexion = False
				

	@api.model
	def _get_view(self, view_id=None, view_type='form', **options):
		"""
		Overrides orm field_view_get.
		@return: Dictionary of Fields, arch and toolbar.
		"""

		arch, view = super()._get_view(view_id, view_type, **options)

		company_name = self.env.user.company_id.name
		if company_name and 'iconnexion' in company_name.lower():
			if self.user_has_groups('iconnexion_custom.group_iconnexion_icon_admin'):  
				purchase = """<page name="purchase_history" string="Purchase History" invisible="0">"""
				sales = """<page name="sale_history2" string="Sales History" invisible="0">"""
			else:
				purchase = """<page name="purchase_history" string="Purchase Historys"  invisible="1" modifiers="{&quot;invisible&quot;: true}">"""
				sales = """<page name="sale_history2" string="Sales Historys"  invisible="1" modifiers="{&quot;invisible&quot;: true}">"""
			arch = arch.replace(str("""<page name="purchase_history" string="Purchase History">"""),purchase )
			# arch = arch.replace(str("""<page name="sale_history2" string="Sales History">"""),sales )
			#due salesman need see sales history
		
		return arch, view

	def _create_coo(self, coo):
		create_coo = True
		if self.coo_id:
			if self.coo_id.name == coo:
				create_coo= False
		if create_coo:
			coo_ids = self.env['icon.coo'].search([('name', '=', coo)],limit=1)
			if coo_ids:
				self.write({'coo_id' : coo_ids.id})
			else:
				coo_id = self.env['icon.coo'].create({'name': coo})
				self.write({'coo_id' : coo_id.id})
			#disable first by david 29 APril 2022 due this field use to report by
			# report_to_user_ids = self.env.user.report_to_user_ids
			# for user_id in report_to_user_ids:
			# 	self.activity_schedule('iconnexion_custom.mail_activity_data_icon_update_coo',user_id=user_id.id)  
		return True
		
	def write(self, values):
		company_name = self.env.user.company_id.name
		if company_name and 'iconnexion' in company_name.lower():
			if self.user_has_groups('iconnexion_custom.group_iconnexion_icon_salesman'):  
				raise UserError(_("Salesman cannot change the product master."))
		return super().write(values)


class Product(models.Model):
	_inherit = "product.product"


	coo_id = fields.Many2one(related="product_tmpl_id.coo_id", string="COO Reference", tracking=True)
	#history
	icon_sales_history_ids = fields.One2many('icon.sales.history','product_id', string="Sales History")
	old_sales_history_ids = fields.One2many('icon.old.sales.history', 'product_id', string="Old Sales History")
	old_quote_history_ids = fields.One2many('icon.old.quote.history', 'product_id', string="Old Quotation History")

	@api.model
	def _get_view(self, view_id=None, view_type='form', **options):
		"""
		Overrides orm field_view_get.
		@return: Dictionary of Fields, arch and toolbar.
		"""

		arch, view = super()._get_view(view_id, view_type, **options)

		company_name = self.env.user.company_id.name
		if company_name and 'iconnexion' in company_name.lower():
			if self.user_has_groups('iconnexion_custom.group_iconnexion_icon_admin'):  
				purchase = """<page name="purchase_history" string="Purchase History" invisible="0">"""
				sales = """<page name="sale_history2" string="Sales History" invisible="0">"""
			else:
				purchase = """<page name="purchase_history" string="Purchase Historys"  invisible="1" modifiers="{&quot;invisible&quot;: true}">"""
				sales = """<page name="sale_history2" string="Sales Historys"  invisible="1" modifiers="{&quot;invisible&quot;: true}">"""
			arch = arch.replace(str("""<page name="purchase_history" string="Purchase History">"""),purchase )
			arch = arch.replace(str("""<page name="sale_history2" string="Sales History">"""),sales )

		
		return arch, view

	def write(self, values):
		company_name = self.env.user.company_id.name
		if company_name and 'iconnexion' in company_name.lower():
			if self.user_has_groups('iconnexion_custom.group_iconnexion_icon_salesman'):  
				raise UserError(_("Salesman cannot change the product master."))
		return super().write(values)

	# cr.execute('CREATE INDEX product_product_icon_id_ref_idx ON product_product (barcode, type)')

	@api.model
	def get_all_products_by_barcode(self):
		# now = datetime. datetime. now()
		# print (now. strftime("%Y-%m-%d %H:%M:%S"),'X')
		products = self.env['product.product'].search_read(
			[('barcode', '!=', None), ('type', '!=', 'service')],
			['barcode', 'display_name', 'uom_id', 'tracking']
		)
		# now = datetime. datetime. now()
		# print (now. strftime("%Y-%m-%d %H:%M:%S"),'V')
		packagings = self.env['product.packaging'].search_read(
			[('barcode', '!=', None), ('product_id', '!=', None)],
			['barcode', 'product_id', 'qty']
		)
		# now = datetime. datetime. now()
		# print (now. strftime("%Y-%m-%d %H:%M:%S"),'W')
		move_ids = self.env['stock.move'].search_read(
			[('state', '=', 'assigned'), ('product_id', '!=', None)],
			['name', 'product_id']
		)
		#
		# for each packaging, grab the corresponding product data
		to_add = []
		to_read = []
		products_by_id = {product['id']: product for product in products}
		for move in move_ids:
			move['barcode'] = move.pop('name')
			to_read.append((move, move['product_id'][0]))
		for packaging in packagings:
			if products_by_id.get(packaging['product_id']):
				product = products_by_id[packaging['product_id']]
				to_add.append(dict(product, **{'qty': packaging['qty']}))
			# if the product doesn't have a barcode, you need to read it directly in the DB
			to_read.append((packaging, packaging['product_id'][0]))
		products_to_read = self.env['product.product'].browse(list(set(t[1] for t in to_read))).sudo().read(['display_name', 'uom_id', 'tracking'])
		products_to_read = {product['id']: product for product in products_to_read}
		to_add.extend([dict(t[0], **products_to_read[t[1]]) for t in to_read])
		# select product_id where stock_move state = 'assigned'
		# now = datetime. datetime. now()
		return {product.pop('barcode'): product for product in products + to_add}

class StockMoveLine(models.Model):
	_inherit = "stock.move.line"

	coo = fields.Char("COO")
	# dc = fields.Date("DC")
	no = fields.Integer("No")
	dc = fields.Char("DC")
	customer_part_number = fields.Char("Cust. P/N")
	dimension = fields.Char("Dimension")
	dimension_length = fields.Char("Dimension (L)")
	dimension_width = fields.Char("Dimension (W)")
	dimension_height = fields.Char("Dimension (H)")
	weight = fields.Char("Weight")
	source_po_id = fields.Many2one('purchase.order',compute='_compute_source_po',string='PO Origin')

	def _compute_source_po(self):
		for move in self:
			move.source_po_id = False
			if move.move_id:
				if move.move_id.purchase_line_id:
					if move.move_id.purchase_line_id.order_id:
						move.source_po_id = move.move_id.purchase_line_id.order_id.id

class ProductBrand(models.Model):

	_inherit = "product.brand"

	# icon_product_manager_ids = fields.Many2many('res.users', 'product_company_partners_rel','product_company_id','partner_id', string="Product Manager")
	icon_product_partner_manager_ids = fields.Many2many('res.partner', 'product_partner_company_partners_rel','product_company_id','partner_id', string="Product Manager")
	company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company.id)
	is_iconnexion = fields.Boolean(string="iConnexion Company", compute='compute_is_iconnexion', store=True)

	@api.depends('company_id')
	def compute_is_iconnexion(self):
		for lead in self:
			company_name = lead.company_id.name
			if company_name and 'iconnexion' in company_name.lower():
				lead.is_iconnexion = True
			else:
				lead.is_iconnexion = False

class SupplierInfo(models.Model):
	_inherit = "product.supplierinfo"

	customer_id = fields.Many2one('res.partner', 'Customer')
	sale_price = fields.Float('Sale Price', digits='Product Price', required=True, help="The price to Sale a product")
	moq = fields.Float('MOQ')


# v16: odes.product.purchase from odes_accounting (uninstallable); class disabled
# class OdesProductPurchase(models.Model):
# 	_inherit = "odes.product.purchase"
# 	amount = fields.Float('Amount')
