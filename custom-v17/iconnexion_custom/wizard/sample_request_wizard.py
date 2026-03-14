from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast


class SampleRequestWizard(models.TransientModel):
	_name = "sample.request.wizard"
	_description = "Sample Request Wizard"


	def action_sample_request_create(self):
		sample_obj = self.env['crm.lead'] 
		samples = sample_obj.browse(self._context.get('active_ids', []))
		for sample in samples:
			sample.get_sample_request()
			action = self.env.ref('iconnexion_custom.action_sample_request_form').read()[0]
			context = {'default_crm_id' : sample.id,}
			domain = [('crm_id','=', sample.id,)]
			action['context'] = context
			action['domain'] = domain
			print(action)
			return action

	def action_sample_request_view(self):
		sample_obj = self.env['crm.lead'] 
		samples = sample_obj.browse(self._context.get('active_ids', []))                                            
		for sample in samples:
			print("sample:::",sample.id)
			action = self.env.ref('iconnexion_custom.action_sample_request_form').read()[0]
			context = {'default_crm_id' : sample.id,}
			domain = [('crm_id','=', sample.id,)]
			action['context'] = context
			action['domain'] = domain
			print(action)
			return action
