# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression




class Attachment(models.Model):
    _inherit = "ir.attachment"

    mccoy_attach_id = fields.Integer("McCoy Attach")


    @api.model_create_multi
    def create(self, vals_list):
        records = super(Attachment, self).create(vals_list)
        for attach in records:
            if attach.website_id and attach.mimetype and 'image/' in attach.mimetype:
                attach.write({'public': True})
        return records
