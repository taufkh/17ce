# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class Lead(models.Model):
    _inherit = 'crm.lead'

    #function to skip NDA
    def _compute_is_skip_nda(self):
        bypass_nda = self.env['ir.config_parameter'].sudo().get_param('odes_crm.bypass_nda')
        for lead in self:
            lead.is_skip_nda = bypass_nda

    is_skip_nda = fields.Boolean(compute="_compute_is_skip_nda", string="Skip NDA")    

    def skip_nda(self):
        self.is_nda_confirmed = True