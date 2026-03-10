##############################################################################
#
#       Copyright © SUREKHA TECHNOLOGIES PRIVATE LIMITED, 2020.
#
#	    You can not extend,republish,modify our code,app,theme without our
#       permission.
#
#       You may not and you may not attempt to and you may not assist others
#       to remove, obscure or alter any intellectual property notices on the
#       Software.
#
##############################################################################
from collections import OrderedDict
from odoo import models, fields, _


class ProductTemplate(models.Model):

    _inherit = "product.template"

    product_brand_id = fields.Many2one('product.brand', string="Product Brand")


    def get_variant_groups(self):
        res = OrderedDict()
        for var in self.valid_product_template_attribute_line_ids:
            res.setdefault(var.attribute_id.category_id.name or _('Uncategorized'), []).append(var)
        return res
