import logging
import math
import re
import time
import traceback

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None

CURRENCY_DISPLAY_PATTERN = re.compile(r'(\w+)\s*(?:\((.*)\))?')


class Currency(models.Model):
    _inherit = "res.currency"

    rounding_decimal = fields.Float(string='Rounding Factor Decimal', digits=(12, 6), default=0.01, help='The decimal value used for rounding calculations.')

    @api.depends('rounding_decimal')
    def _compute_decimal_places(self):
        for currency in self:
            if 0 < currency.rounding_decimal < 1:
                currency.decimal_places = int(math.ceil(math.log10(1/currency.rounding_decimal)))
            else:
                currency.decimal_places = 0

