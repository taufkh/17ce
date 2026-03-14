from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast

class IconQuotationApproveWizard(models.TransientModel):
	_inherit = "icon.quotation.approve.wizard"


	def button_approve(self):
		partner_ids = []
		# supplier_ids = self.env['product_id'].search([('id', '=', self.sale_line_id.product_id.id)])
		if self.sale_line_id.product_id.product_brand_id:
			for partner_id in self.sale_line_id.product_id.product_brand_id.icon_product_partner_manager_ids:
				partner_ids.append(partner_id.id)
				
		self.sale_line_id.order_id.with_context(force_send=True,icon_skip_partner=True).message_post_with_view(
								'iconnexion_custom.so_approve_low_margin',
							values={'sales': self.sale_line_id,},
							subtype_id=self.env.ref('mail.mt_comment').id,message_type='comment',
							partner_ids=partner_ids,
							subject='New Pricing Approve '+ self.sale_line_id.order_id.name,                            
					)
		self.sale_line_id.write({
				'is_lower_margin': False,
				'is_request_margin': False,
				'date_approve': fields.Datetime.now(),
				'approve_user_id': self.env.uid,
				})
		lines = []
		old_price = 0
		if self.sale_line_id.product_id.manufacturing_company_id:
			if self.sale_line_id.product_id.seller_ids:
				customersss = False
				for sup in self.sale_line_id.product_id.seller_ids:

					if sup.customer_id.id == self.sale_line_id.order_id.partner_id.id:
						old_price=sup.sale_price
						customersss = True			
						sup.write({
							'name' : self.sale_line_id.product_id.manufacturing_company_id.id,
							'sale_price' : self.sale_line_id.quote_price_unit,
							'delay' : self.sale_line_id.sale_delay,
							'moq' : self.sale_line_id.moq
							})
				if not customersss :
					vals = {
						'name' : self.sale_line_id.product_id.manufacturing_company_id.id,
						'product_id' : self.sale_line_id.product_id.id,
						'customer_id' : self.sale_line_id.order_id.partner_id.id,
						'sale_price' : self.sale_line_id.quote_price_unit,
						'delay' : self.sale_line_id.sale_delay,
						'moq' : self.sale_line_id.moq,
						'price' : self.sale_line_id.product_id.standard_price,
					}

					lines.append((0, 0, vals))
			else :
				vals = {
					'name' : self.sale_line_id.product_id.manufacturing_company_id.id,
					'product_id' : self.sale_line_id.product_id.id,
					'customer_id' : self.sale_line_id.order_id.partner_id.id,
					'sale_price' : self.sale_line_id.quote_price_unit,
					'delay' : self.sale_line_id.sale_delay,
					'moq' : self.sale_line_id.moq,
					'price' : self.sale_line_id.product_id.standard_price,
				}

				lines.append((0, 0, vals))
			self.sale_line_id.product_id.seller_ids= lines
			self.sale_line_id.product_id.product_tmpl_id.message_post(body="Sale Price for Customer " + self.sale_line_id.order_id.partner_id.name + " has been changed from " + str(old_price) + " to " + str(self.sale_line_id.quote_price_unit) + " Reason " + self.reason)
			
		else:
			raise ValidationError(_("Please Fill the Product's Manufacturing Company"))
	
		
		return True