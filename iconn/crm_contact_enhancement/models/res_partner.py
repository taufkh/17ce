import ast

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _view_get_address(self, arch):
        arch = super()._view_get_address(arch)
        # Hide State/City/ZIP (and city dropdown if present) until a Country is selected
        for field_name in ("state_id", "city", "zip", "city_id"):
            for field_node in arch.xpath(f"//field[@name='{field_name}']"):
                attrs = field_node.get("attrs")
                if attrs:
                    try:
                        attrs_dict = ast.literal_eval(attrs)
                    except Exception:
                        attrs_dict = {}
                else:
                    attrs_dict = {}
                invisible_domain = attrs_dict.get("invisible")
                if invisible_domain:
                    attrs_dict["invisible"] = ["|", ("country_id", "=", False)] + invisible_domain
                else:
                    attrs_dict["invisible"] = [("country_id", "=", False)]
                field_node.set("attrs", repr(attrs_dict))
        # Enforce State -> City -> ZIP order inside address rows
        for address_node in arch.xpath("//div[hasclass('o_address_format')]"):
            state = address_node.find(".//field[@name='state_id']")
            city_id = address_node.find(".//field[@name='city_id']")
            city = address_node.find(".//field[@name='city']")
            zip_field = address_node.find(".//field[@name='zip']")
            row = None
            for field in (state, city_id, city, zip_field):
                if field is not None:
                    row = field.getparent()
                    break
            if row is None:
                continue
            for field in (state, city_id, city, zip_field):
                if field is not None and field.getparent() is not None:
                    field.getparent().remove(field)
            for field in (state, city_id, city, zip_field):
                if field is not None:
                    row.append(field)
        return arch
