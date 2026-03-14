from datetime import datetime, timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast

class IconSalePopupWizard(models.TransientModel):
	_name = "icon.sale.popup.wizard"
	_description = "Sale Popup Wizard"

	# name = fields.Char('Reason')
	reason = fields.Char('Reason')
