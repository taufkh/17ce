from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    documents_fleet_model = fields.Char(string='Linked Model')
    documents_fleet_res_id = fields.Integer(string='Linked Record ID')
