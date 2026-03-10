from odoo import fields, models, tools

class IconSalesHistory(models.Model):
    _inherit = "icon.sales.history"
    
    def _select(self):
        select_str = """
            SELECT
            sol.id as id,
            sol.order_id as order_id,
            sol.product_id as product_id,
            pp.product_tmpl_id as product_tmpl_id,
            so.currency_id as currency_id,
            so.partner_id as partner_id,
            sol.price_unit as price_unit,
            sol.price_subtotal as price_subtotal,
            sol.product_uom_qty as qty,
            so.user_id as user_id,
            so.date_order as date
        """
        return select_str    

    def _from(self):
        from_str = """
            FROM sale_order_line sol
            LEFT JOIN sale_order as so ON so.id = sol.order_id
            LEFT JOIN product_product as pp ON pp.id = sol.product_id
            WHERE so.state = 'sale'
        """
        return from_str

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as
            %s
            
            %s
        """ % (self._table, self._select(), self._from()))

class IconQuotationHistory(models.Model):
    _name = "icon.quotation.history"
    _description = "Quotation History"
    _auto = False
    _rec_name = 'order_id'

    order_id = fields.Many2one('sale.order', string="Sale Order", readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string="Product Template", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    price_unit = fields.Float('Unit Price', readonly=True)
    price_subtotal = fields.Float('Amount', readonly=True)
    qty = fields.Float('EAU', readonly=True)
    user_id = fields.Many2one('res.users', string="Salesperson", readonly=True)
    date = fields.Datetime('Date', readonly=True)
    moq = fields.Float('MOQ', readonly=True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)


    def _select(self):
        select_str = """
            SELECT
                    sol.id as id,
                    sol.order_id as order_id,
                    sol.product_id as product_id,
                    pp.product_tmpl_id as product_tmpl_id,
                    so.currency_id as currency_id,
                    so.partner_id as partner_id,
                    sol.price_unit as price_unit,
                    sol.price_subtotal as price_subtotal,
                    sol.product_uom_qty as qty,
                    sol.moq as moq,
                    sol.state as state,
                    so.user_id as user_id,
                    so.date_order as date
        """
        return select_str    

    def _from(self):
        from_str = """
            FROM sale_order_line sol
            LEFT JOIN sale_order as so ON so.id = sol.order_id
            LEFT JOIN product_product as pp ON pp.id = sol.product_id
            WHERE so.state = 'draft' OR (so.state ='done' AND so.name LIKE '%QUO%')
        """
        return from_str

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as
            %s
            
            %s
        """ % (self._table, self._select(), self._from()))