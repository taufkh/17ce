from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError


class AccountPaymentTerm(models.Model):
	_inherit = 'account.payment.term'
	

	payment_term_type = fields.Selection(selection=[('advance_to_process', 'TT In Advance to Process Order'), ('advance_before_delivery', 'TT In Advance Before Delivery'), ('partial_before_delivery_term', 'Partial Before Delivery'), ('partial_cod_term', 'Partial COD')], string='Payment Term Type')
	dep_paid_1st = fields.Float(string='1st Dep Paid (%)')
	dep_paid_2nd = fields.Float(string='2nd Dep Paid (%)')