from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    documents_default_mailing_settings = fields.Boolean()
    document_mailing_list_id = fields.Many2one('mailing.list', string="Default Document")

  
