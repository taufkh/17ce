# -*- encoding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.parser import parse


class MccoySpecialExportWizard(models.TransientModel):
    _name = "mccoy.special.export.wizard"
    _description = "McCoy Special Export Wizard"

    name = fields.Char(string="Name",default="Special Export")
    product_template_ids = fields.Many2many("product.template",string="Product Template")
    product_ids = fields.Many2many("product.product",string="Product")


    @api.model
    def default_get(self, fields):
        vals = super(MccoySpecialExportWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_model == 'product.template':
            vals['product_template_ids'] = [(6, 0, active_ids)]
        elif active_model == 'product.product':
            vals['product_ids'] = [(6, 0, active_ids)]
        return vals



    def export(self):
        if self.product_template_ids:
            return {                   'name'     : 'Export',
                  'res_model': 'ir.actions.act_url',
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'self',
                  'url'      : "/web/export_product_xlsx?data_id="+str(self.id)
               }
        elif self.product_ids:
            return {                   'name'     : 'Export',
                  'res_model': 'ir.actions.act_url',
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'self',
                  'url'      : "/web/export_product_xlsx?data_id="+str(self.id)
               }
        return True
