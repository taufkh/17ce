# -*- coding: utf-8 -*-

import logging
import psycopg2

from odoo import api, fields, models, registry, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    is_delivery_method = fields.Boolean(string='Delivery Method')