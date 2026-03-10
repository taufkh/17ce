# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    documents_default_mailing_settings = fields.Boolean(related='company_id.documents_default_mailing_settings', readonly=False,
                                                string="Document Default Mailing")
    document_mailing_list_id = fields.Many2one('mailing.list', related='company_id.document_mailing_list_id', readonly=False,
                                     string="document default workspace")
