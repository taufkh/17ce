from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_is_zero, float_compare



class SaleOrder(models.Model):
    _inherit = "sale.order"

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
    request_date = fields.Datetime('Request Date')
    promise_date = fields.Datetime('Promise Date')
    contact_name = fields.Char('Contact Name', compute='_get_contact')
    contact_phone = fields.Char('Contact Phone', compute='_get_contact')
    invoice_forecats_line_ids = fields.One2many('sale.invoice.forecast', 'sale_id',string="Invoice Forecasted")
    
    	
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        self.ensure_one()
        company = self.company_id
        quotation_type = self.quotation_type
        if quotation_type == 'service' and company.service_journal_id:
            res['journal_id'] = company.service_journal_id.id
        elif quotation_type == 'item' and company.component_journal_id:
            res['journal_id'] = company.component_journal_id.id

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    request_date = fields.Datetime('Request Date')
    promise_date = fields.Datetime('Promise Date')

    # @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'untaxed_amount_to_invoice')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        ***Modified so that this function accomodate move line from split by line
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.move_type == 'out_invoice':
                        if invoice_line.is_split_by_line_downpayment:
                            continue
                        qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                    elif invoice_line.move_id.move_type == 'out_refund':
                        if not line.is_downpayment or line.untaxed_amount_to_invoice == 0 :
                            qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
            #add count +1 if invoice is downpaymetn without invoice lines, to allow downpayment to be counted
            if line.is_downpayment and not len(line.invoice_lines):
                qty_invoiced += 1
            line.qty_invoiced = qty_invoiced


class SaleInvoiceForecast(models.Model):
    _name = 'sale.invoice.forecast'
    _description = 'Sale Invoice Forecast'

    date_invoice = fields.Date('Date')
    request_date = fields.Datetime('Request Date')
    amount = fields.Float('Amount')
    sale_id = fields.Many2one('sale.order',string="Sale")
