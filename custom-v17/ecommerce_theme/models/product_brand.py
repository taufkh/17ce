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
from odoo import models, fields


class ProductBrand(models.Model):

    _name = "product.brand"
    _description = "Product Brand"

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    image = fields.Binary('Image')
