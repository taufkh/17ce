import ast

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _view_get_address(self, arch):
        arch = super()._view_get_address(arch)
        # Hide city dropdown until state is selected
        for city_field in arch.xpath("//field[@name='city_id']"):
            attrs = city_field.get("attrs")
            if attrs:
                try:
                    attrs_dict = ast.literal_eval(attrs)
                except Exception:
                    attrs_dict = {}
            else:
                attrs_dict = {}
            invisible_domain = attrs_dict.get("invisible")
            if invisible_domain:
                attrs_dict["invisible"] = ["|", ("state_id", "=", False)] + invisible_domain
            else:
                attrs_dict["invisible"] = [("state_id", "=", False)]
            city_field.set("attrs", repr(attrs_dict))
        return arch
