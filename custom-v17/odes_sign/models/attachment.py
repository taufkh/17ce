
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict, defaultdict


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    sale_id = fields.Many2one('sale.order', 'Sale')