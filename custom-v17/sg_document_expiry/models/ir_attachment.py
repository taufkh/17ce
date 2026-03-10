# -*- coding: utf-8 -*-

from odoo import api, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') == 'report.sg_document_expiry.document_expirey_report.pdf':
                vals.update({
                    'name': 'Document Expiry Report.pdf',
                })
        return super(IrAttachment, self).create(vals_list)
