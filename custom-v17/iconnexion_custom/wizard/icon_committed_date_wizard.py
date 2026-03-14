from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class IconCommittedDateWizard(models.TransientModel):
	_name = "icon.committed.date.wizard"
	_description = "iConnexion Committed Date Wizard"

	sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
	date = fields.Datetime('Date',default=fields.Datetime.now())
	change_reason = fields.Char('Reason')

	@api.model
	def default_get(self, fields):
		res = super(IconCommittedDateWizard, self).default_get(fields)
		active_ids = self.env.context.get('active_ids', [])
		context = dict(self._context or {})
		active_id = context.get('active_id')
		res['sale_line_id'] = active_ids[0]
		
		return res

   

	def action_change_date(self):
		context = dict(self._context or {})
		active_model = context.get('active_model')
		active_id = context.get('active_id')

		# line_obj = self.env['sale.order.line']
		# line_search = line_obj.search([('id', '=', active_id)])
		history_obj = self.env['icon.committeddate.history']
		for line in self.sale_line_id:
			line.write({
				'committed_date': self.date
				})            
			# line._track_date_received(self.date.strftime('%Y-%m-%d  %H:%M:%S'))
			history_obj.create({
				'sale_line_committeddate_history_id': line.id,
				'date': self.date,
				'change_reason': self.change_reason
				})
	#buat tombol untuk view history
