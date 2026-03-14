from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    documents_product_model = fields.Char(string='Linked Model')
    documents_product_res_id = fields.Integer(string='Linked Record ID')
