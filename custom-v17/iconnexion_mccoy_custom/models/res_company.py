import re
import base64
import logging
import requests


from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools import partition, pycompat
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)



class ResCompany(models.Model):
	_inherit = 'res.company'
	
	company_customer_tax_product_id = fields.Many2one('account.tax', help="Default taxes used when selling the product.", string='Product Customer Taxes', domain=[('type_tax_use', '=', 'sale')])
	company_sequence_customer_credit_note_id = fields.Many2one('ir.sequence', help="Default Running Number for Credit Note", string='Customer Credit Note Sequence')
	company_sequence_income_input_id = fields.Many2one('ir.sequence', help="Default Running Number for Income Input", string='Income Input Sequence')
	delivery_method_id = fields.Many2one('delivery.carrier', string='Default Delivery Method')
	freight_term_id = fields.Many2one('delivery.carrier', string='Default Freight Term')
	debit_note_sequence_id = fields.Many2one('ir.sequence', string='Default Debit Note Sequence')
	vendor_credit_note_sequence_id = fields.Many2one('ir.sequence', string='Default Vendor Credit Note Sequence')
	delivery_order_invoice_sequence_id = fields.Many2one('ir.sequence', string='Default Delivery Order Invoice Sequence')
	delivery_order_invoice_taiwan_sequence_id = fields.Many2one('ir.sequence', string='Default Delivery Order Invoice Taiwan Sequence')
	delivery_order_invoice_india_sequence_id = fields.Many2one('ir.sequence', string='Default Delivery Order Invoice India Sequence')
	redeem_sg_api_url = fields.Char(string="Redeem SG API Url")
	redeem_sg_api_key = fields.Char(string="Redeem SG API Key")
	redeem_sg_response = fields.Char(string="Redeem SG Response")
	current_tax = fields.Char(string="Current Tax")

	def make_redeem_sg_api_request(self):
		headers = {
			"x-api-key": self.redeem_sg_api_key,
			'Content-Type': 'application/json',
		}
		request_body = {
			"qr": "rsg:v_NGHYEoRLe9ulZVhJ2ML6o",
			"metadata": "branch_code:123,pos_ID:456,cashier_ID:001,receipt_number:789,SKU:001,002",
		}

		response = requests.post(self.redeem_sg_api_url, json=request_body, headers=headers)

		self.write({'redeem_sg_response': response.json()})
