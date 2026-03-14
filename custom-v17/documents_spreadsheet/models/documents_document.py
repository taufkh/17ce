from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    documents_spreadsheet_model = fields.Char(string='Linked Model')
    documents_spreadsheet_res_id = fields.Integer(string='Linked Record ID')
