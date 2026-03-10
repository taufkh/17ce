# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'
	
	company_customer_tax_product_id = fields.Many2one(related='company_id.company_customer_tax_product_id', readonly=False)
	company_sequence_customer_credit_note_id = fields.Many2one(related='company_id.company_sequence_customer_credit_note_id', readonly=False)
	company_sequence_income_input_id = fields.Many2one(related='company_id.company_sequence_income_input_id', readonly=False)
	delivery_method_id = fields.Many2one(related='company_id.delivery_method_id', readonly=False)
	freight_term_id = fields.Many2one(related='company_id.freight_term_id', readonly=False)
	debit_note_sequence_id = fields.Many2one(related='company_id.debit_note_sequence_id', readonly=False)
	vendor_credit_note_sequence_id = fields.Many2one(related='company_id.vendor_credit_note_sequence_id', readonly=False)
	delivery_order_invoice_sequence_id = fields.Many2one(related='company_id.delivery_order_invoice_sequence_id', readonly=False)
	delivery_order_invoice_taiwan_sequence_id = fields.Many2one(related='company_id.delivery_order_invoice_taiwan_sequence_id', readonly=False)
	delivery_order_invoice_india_sequence_id = fields.Many2one(related='company_id.delivery_order_invoice_india_sequence_id', readonly=False)
	current_tax = fields.Char(related='company_id.current_tax', readonly=False)