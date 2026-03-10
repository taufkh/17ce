from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    def _get_contact(self):
        for partner in self:
            for child in partner.partner_id:
                child_name = False
                phone = False
                for po in child.child_ids:
                    child_name = po.name
                    phone = po.phone
        partner.contact_name = child_name
        partner.contact_phone = phone

    freight_terms = fields.Char('Freight Terms (Text)')
    remarks = fields.Text('remarks')
    contact_name = fields.Char('Contact Name', compute='_get_contact')
    contact_phone = fields.Char('Contact Phone', compute='_get_contact')
