from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    sign_request_id = fields.Many2one('sign.request', string='Sign Request')
