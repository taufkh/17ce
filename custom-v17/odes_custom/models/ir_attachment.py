
import logging
import threading
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict, defaultdict


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    datas_view = fields.Binary(compute='_get_datas_view')
    datas_image = fields.Binary(compute='_get_datas_view')
    crm_lead_id = fields.Many2one('crm.lead', 'CRM Lead')
    po_type_id = fields.Many2one('po.type', 'Po Type')

    def _get_datas_view(self):
        self.datas_view = self.datas
        self.datas_image = self.datas