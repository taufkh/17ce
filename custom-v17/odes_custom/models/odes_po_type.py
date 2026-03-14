from odoo import api, fields, models

class OdesPoType(models.Model):
    _name = "po.type"
    _description = "PO Type"

    name = fields.Char('PO Type')
