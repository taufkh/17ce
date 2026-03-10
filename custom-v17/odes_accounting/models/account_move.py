from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang



class AccountMove(models.Model):
    _inherit = "account.move"


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
    
    def _get_subtotal(self):
        for inv in self:
            invoice_subtotal = 0
            for line in inv.invoice_line_ids:
                if line.product_id.type != 'service':
                    invoice_subtotal += line.price_subtotal
            inv.invoice_subtotal = invoice_subtotal

    def _get_downpayment(self):
        for inv in self:
            invoice_downpayment = 0
            for line in inv.invoice_line_ids:
                if line.product_id.type == 'service':
                    invoice_downpayment += abs(line.price_subtotal)
            inv.invoice_downpayment = invoice_downpayment

    def _get_percentage(self):
        for x in self:
            percentage_downpayment = 0
            for line in x.invoice_line_ids:
                if line.product_id.type == 'service':
                    percentage_downpayment += (line.price_subtotal / (-50)) * 100
            x.percentage_downpayment = percentage_downpayment

    delivery_terms = fields.Char('Delivery Terms')

    amount_unbalance = fields.Float('Amount Unbalance')
    est_del_date = fields.Datetime('Est Del Date')
    freight_terms = fields.Char('Freight Terms (Text)')
    invoice_subtotal = fields.Monetary(string='Subtotal', compute='_get_subtotal')
    invoice_downpayment = fields.Monetary(string='Down Payment', compute='_get_downpayment')
    percentage_downpayment = fields.Float(string='Percetage Downpayment', compute='_get_percentage')
    contact_name = fields.Char('Contact Name', compute='_get_contact')
    contact_phone = fields.Char('Contact Phone', compute='_get_contact')
        
    
    def _get_starting_sequence(self):
        self.ensure_one()
        
        starting_sequence = "%s/%04d/%02d/0000" % (self.journal_id.code, self.date.year, self.date.month)
        if self.journal_id.refund_sequence and self.move_type in ('out_refund', 'in_refund'):
            # starting_sequence = "R" + starting_sequence
            if self.move_type == 'out_refund':
                year = str(self.date.year)
                year = year[-2:]
                starting_sequence = "%s0000" % ('CN')
            else:
                year = str(self.date.year)
                year = year[-2:]
                starting_sequence = "%s0000" % ('DN')

            
            
        if self.journal_id.type == 'sale' and self.move_type in ('out_invoice'):
            year = str(self.date.year)
            year = year[-2:]
            starting_sequence = "%s/%s/0000" % (self.journal_id.code, year)
            
        # print (starting_sequence, 'starting_sequence')
        return starting_sequence

    def get_quotation_no(self):
        res = ""
        so = self.invoice_line_ids.sale_line_ids.order_id.quotation_sale_id
        if so:
            res = so[0].name
        return res

    def get_sgd_value(self, value):
        self.ensure_one()
        currency = self.currency_id
        sg_currency = self.env.ref('base.SGD')
        if currency == sg_currency:
            return value
        else:
            return currency._convert(value, sg_currency, self.company_id, self.invoice_date or fields.Date.today(), round=False)

    def unlink(self):
        downpayment_lines = self.mapped('line_ids.sale_line_ids').filtered(lambda line: line.is_downpayment and line.invoice_lines <= self.mapped('line_ids'))
        dont_delete = False
        for line in downpayment_lines:
            if line.qty_invoiced < 0:
                dont_delete = True
        if dont_delete:
            raise UserError(_("Cannot be delete, The invoice has been deduct with down payment."))

        res = super(AccountMove, self).unlink()
        return res


    def recompute_line(self):

        # render = self.with_context(recompute_line_item=True).write()
        current_invoice_lines = self.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)
        others_lines = self.line_ids - current_invoice_lines
        if others_lines and current_invoice_lines - self.invoice_line_ids:
            others_lines[0].recompute_tax_line = True
        self.line_ids = others_lines + self.invoice_line_ids
        self._onchange_recompute_dynamic_lines()
        
        # for invoice in self:
        #     for line in invoice.invoice_line_ids:
        #         line.write({'price_unit' : 1000})

        #     invoice.update(invoice.invoice_line_ids)


    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(self.env['account.move.line']._fields)
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
            print (sums)
            self.write({'amount_unbalance' : sums[0]})
        else:
            self.write({'amount_unbalance' : 0})
            
            # raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))




    # def write(self, vals):
    #     self.with_context(recompute_line_data=True).recompute_line()
    #     res = super(AccountMove, self).write(vals)
    #     return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_split_by_line_downpayment = fields.Boolean('Split Line DP')    



## Community-safe: account.asset model is not available without account_asset.

    
