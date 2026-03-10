from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang



class StockPicking(models.Model):
    _inherit = "stock.picking"
    
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
    
    payment_terms = fields.Char('Payment Terms')
    freight_terms = fields.Char('Freight Terms (Text)')
    contact_name = fields.Char('Contact Name', compute='_get_contact')
    contact_phone = fields.Char('Contact Phone', compute='_get_contact')

    flight_vessel = fields.Char('Flight / Vessel')
    awb = fields.Char('AWB #')
    by_courier = fields.Char('By')
    sailing_on = fields.Char('Sailing on/about')
    total_packages = fields.Integer('Total Packages')
    container_no = fields.Char('Container No')
    seal_no = fields.Char('Seal No')
    shipping_mark = fields.Char('Shipping Mark')


class StockMove(models.Model):
    _inherit = "stock.move"

    qty_ctn = fields.Float('Quantity/Ctn')
    no_of_carton = fields.Integer('No of cartons')
    measurement = fields.Char('Measurement (CM)')
    weight_ctn = fields.Integer('Weight/Ctn')
    total_gr_wt = fields.Float('Total Gr. Wt.')
