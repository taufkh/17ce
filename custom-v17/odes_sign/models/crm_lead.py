
import logging
import threading
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict, defaultdict
from dateutil.parser import parse


class Lead(models.Model):
    _inherit = 'crm.lead'

    def action_view_sale_quotation(self):
        res = super(Lead, self).action_view_sale_quotation()
        

        res['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id,
            'default_is_current': 1,
            'search_default_is_current': 1,
            'default_pricelist_id': self.partner_id.property_product_pricelist.id,
            # 'default_so_type': 'sf',
        }
        

        return res
