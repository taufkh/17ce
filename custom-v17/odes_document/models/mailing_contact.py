from odoo import fields, models, api, _


class MassMailingContact(models.Model):
    _inherit = 'mailing.contact'

    phone = fields.Char('Phone')

  
