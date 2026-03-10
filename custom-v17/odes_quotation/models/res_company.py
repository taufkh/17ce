# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class Company(models.Model):
    _inherit = 'res.company'

    def _default_quotation_description(self):
    	return """
    		<p>I am pleased to submit this quotation for the Business Consultancy, Design, Development and Implementation of a fully integrated customized workflow driven Business Solution using Mccoy On-Demand Enterprise Solution.</p><p><br></p><p>Please refer to Appendix A for the breakdown of the quotation. This quotation does not include any hardware components.</p><p><br></p><p><b>Terms and Conditions:</b></p><p>1) This quotation is valid for 30 days.</p><p>2) All prices quoted are before GST or any other applicable taxes such as withholding tax in a foreign country as and when applicable.</p><p>3) Payment terms :</p><p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; a) 30% on acceptance of this quotation,</p><p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;b) 10% per month thereafter for 6 months,</p><p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;c) Remaining 10% within 14days after project Go Live.</p><p>4) To accept the quotation, client will issue purchase order or make payment to our respective sales.</p><p>5) If payment is not received in accordance to payment terms as agreed, Mccoy Pte Ltd reserves the right not to carry on the service and the client agrees to the following terms :</p><p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;a) Not to hold Mccoy Pte Ltd for any disruption of services this termination may cause.</p><p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;b) To pay for services rendered up to the point of the termination including fees in lieu of notice.</p>
    	"""

    def _default_quotation_timeline_remark(self):
    	return """
    		<p>(Inclusive of Estimated Customization – This will be refined after conducting the Detailed Requirement Study)</p>
    	"""

    def _default_quotation_product_id(self):
    	return self.env.ref('odes_quotation.service_product_0', raise_if_not_found=False)

    quotation_description = fields.Text('Description', default=_default_quotation_description)
    quotation_timeline_remark = fields.Text('Timeline Remark', default=_default_quotation_timeline_remark)
    quotation_default_product_id = fields.Many2one('product.product', 'Default Product', default=_default_quotation_product_id)
    quotation_to_company_id = fields.Many2one('res.company', 'To Company')
    quotation_prefix_id = fields.Many2one('ir.sequence', 'Prefix')
    quotation_old_prefix = fields.Char('Old Prefix')
    quotation_new_prefix = fields.Char('New Prefix')

    quotation_report_template = fields.Many2one('ir.actions.report', 'Optional report to print and attach')

    def action_convert_existing_mccoy_quotation_number(self):
        sale_obj = self.env['sale.order']
        sales = sale_obj.search([('company_id', '=', 2)])
        for sale in sales:
            if 'SO21' in sale.name:
                name = sale.name
                create_date = sale.create_date
                create_date_month = create_date.strftime('%m')
                if sale.state in ('cancel', 'draft', 'sent'):
                    name = name.replace('SO21', 'McCoy-Q21/' + create_date_month + '/')
                if sale.state in ('sale', 'done'):
                    name = name.replace('SO21', 'McCoy-S21/' + create_date_month + '/')

                sale.write({'name': name})