# -*- coding: utf-8 -*- 
import re
import base64
import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools import partition, pycompat
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)



class ResCompany(models.Model):
    _inherit = 'res.company'
    
    
    fax = fields.Char('Fax')
    remarks = fields.Text('Remarks')
    remarks_header = fields.Text('Remarks Header')

    service_journal_id = fields.Many2one('account.journal', 'Service Journal')
    component_journal_id = fields.Many2one('account.journal', 'Component Journal')
    
    def write_partner(self):
        
        self.env.cr.execute("""select id from res_partner where company_id = %s""",(self.id,))
        result = self.env.cr.fetchall()
        
        for partner_id in result:
            partner = self.env['res.partner'].browse(partner_id[0])
            partner.write({'is_updated_data' : True})
            
    def write_product(self):
        """
        Generate the journal representing this company_period.
        """
        self.ensure_one()
        self.env.cr.execute("""select id from product_template where company_id = %s""",(self.id,))
        result = self.env.cr.fetchall()
        if result:
            product_tmpl_ids = [x[0] for x in result]
            product = self.env['product.template'].browse(product_tmpl_ids)
            product.write({'is_updated_data' : True})
        
            
            
    
    

#class AccountMove(models.Model):
#	_inherit = 'account.move'
#
##	invoice_no = fields.Char('Invoice No')
#	delivery_terms = fields.Char('Delivery Terms')
		